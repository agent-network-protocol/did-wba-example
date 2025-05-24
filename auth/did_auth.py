"""
DID WBA authentication module with both client and server capabilities.
"""

import json
import logging
import traceback
import secrets
import aiohttp
from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import Request, HTTPException
from agent_connect.authentication import (
    verify_auth_header_signature,
    resolve_did_wba_document,
    extract_auth_header_parts,
    create_did_wba_document,
    DIDWbaAuthHeader,
)

from auth.custom_did_resolver import resolve_local_did_document

from core.config import settings
from auth.token_auth import create_access_token

# Store server-generated nonces
VALID_SERVER_NONCES: Dict[str, datetime] = {}


def is_valid_server_nonce(nonce: str) -> bool:
    """
    Check if a nonce is valid and not expired.
    Each nonce can only be used once (proper nonce behavior).

    Args:
        nonce: The nonce to check

    Returns:
        bool: Whether the nonce is valid
    """
    current_time = datetime.now(timezone.utc)
    
    # Clean up expired nonces first
    expired_nonces = [
        n for n, t in VALID_SERVER_NONCES.items()
        if current_time - t > timedelta(minutes=settings.NONCE_EXPIRATION_MINUTES)
    ]
    for n in expired_nonces:
        del VALID_SERVER_NONCES[n]
    
    # If nonce was already used, reject it
    if nonce in VALID_SERVER_NONCES:
        logging.warning(f"Nonce already used: {nonce}")
        return False
    
    # Mark nonce as used
    VALID_SERVER_NONCES[nonce] = current_time
    logging.info(f"Nonce accepted and marked as used: {nonce}")
    return True


def verify_timestamp(timestamp_str: str) -> bool:
    """
    Verify if a timestamp is within the valid period.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        bool: Whether the timestamp is valid
    """
    try:
        # Parse the timestamp string
        request_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # Get current time
        current_time = datetime.now(timezone.utc)

        # Calculate time difference
        time_diff = abs((current_time - request_time).total_seconds() / 60)

        # Verify timestamp is within valid period
        if time_diff > settings.TIMESTAMP_EXPIRATION_MINUTES:
            logging.error(
                f"Timestamp expired. Current time: {current_time}, Request time: {request_time}, Difference: {time_diff} minutes"
            )
            return False

        return True

    except ValueError as e:
        logging.error(f"Invalid timestamp format: {e}")
        return False
    except Exception as e:
        logging.error(f"Error verifying timestamp: {e}")
        return False


def get_and_validate_domain(request: Request) -> str:
    """
    Get the domain from the request.

    Args:
        request: FastAPI request object

    Returns:
        str: Domain from request host header
    """
    # Get host from request
    host = request.headers.get("host", "")
    domain = host.split(":")[0]
    return domain


async def handle_did_auth(authorization: str, domain: str) -> Dict:
    """
    Handle DID WBA authentication and return token.

    Args:
        authorization: DID WBA authorization header
        domain: Domain for DID WBA verification

    Returns:
        Dict: Authentication result with token

    Raises:
        HTTPException: When authentication fails
    """
    try:
        logging.info(
            f"Processing DID WBA authentication - domain: {domain}, Authorization header: {authorization}"
        )

        # Extract header parts
        header_parts = extract_auth_header_parts(authorization)

        if not header_parts:
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )

        # Unpack order: (did, nonce, timestamp, verification_method, signature)
        did, nonce, timestamp, verification_method, signature = header_parts

        logging.info(f"Processing DID WBA authentication - DID: {did}, Verification Method: {verification_method}")

        # Verify timestamp
        if not verify_timestamp(timestamp):
            raise HTTPException(status_code=401, detail="Timestamp expired or invalid")

        # Verify nonce validity
        if not is_valid_server_nonce(nonce):
            logging.error(f"Invalid or expired nonce: {nonce}")
            raise HTTPException(status_code=401, detail="Invalid or expired nonce")

        # Try to resolve DID document using custom resolver
        did_document = await resolve_local_did_document(did)

        # If custom resolver fails, try using standard resolver
        if not did_document:
            logging.info(f"Local DID resolution failed, trying standard resolver for DID: {did}")
            try:
                did_document = await resolve_did_wba_document(did)
            except Exception as e:
                logging.error(f"Standard DID resolver also failed: {e}")
                did_document = None

        if not did_document:
            raise HTTPException(
                status_code=401, detail="Failed to resolve DID document"
            )

        logging.info(f"Successfully resolved DID document: {did}")

        # Verify signature
        try:
            # Reconstruct the complete authorization header
            full_auth_header = authorization

            # Call verification function
            is_valid, message = verify_auth_header_signature(
                auth_header=full_auth_header,
                did_document=did_document,
                service_domain=domain,
            )

            logging.info(f"Signature verification result: {is_valid}, message: {message}")

            if not is_valid:
                raise HTTPException(
                    status_code=401, detail=f"Invalid signature: {message}"
                )
        except Exception as e:
            logging.error(f"Error verifying signature: {e}")
            raise HTTPException(
                status_code=401, detail=f"Error verifying signature: {str(e)}"
            )

        # Generate access token
        access_token = create_access_token(data={"sub": did})

        logging.info("Authentication successful, access token generated")

        return {"access_token": access_token, "token_type": "bearer", "did": did}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during DID authentication: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Authentication error")


# Client-related functions
async def generate_or_load_did(unique_id: str = None) -> Tuple[Dict, Dict, str]:
    """
    Generate a new DID document or load an existing DID document.

    Args:
        unique_id: Optional user unique identifier

    Returns:
        Tuple[Dict, Dict, str]: Contains DID document, keys, and DID path
    """
    if not unique_id:
        unique_id = secrets.token_hex(8)

    # Check if DID document already exists
    current_dir = Path(__file__).parent.parent.absolute()
    user_dir = current_dir / settings.DID_DOCUMENTS_PATH / f"user_{unique_id}"
    did_path = user_dir / settings.DID_DOCUMENT_FILENAME

    if did_path.exists():
        logging.info(f"Loading existing DID document from {did_path}")

        # Load DID document
        with open(did_path, "r", encoding="utf-8") as f:
            did_document = json.load(f)

        # Create empty keys dictionary since we already have private key file
        keys = {}

        return did_document, keys, str(user_dir)

    # Create DID document
    logging.info("Creating new DID document...")
    host = "localhost"
    did_document, keys = create_did_wba_document(
        hostname=host,
        port=settings.LOCAL_PORT,
        path_segments=["wba", "user", unique_id],
        agent_description_url=f"http://{host}:{settings.LOCAL_PORT}/agents/example/ad.json",
    )

    # Save private key and DID document
    user_dir.mkdir(parents=True, exist_ok=True)

    # Save private key
    for method_fragment, (private_key_bytes, _) in keys.items():
        private_key_path = user_dir / f"{method_fragment}_private.pem"
        with open(private_key_path, "wb") as f:
            f.write(private_key_bytes)
        logging.info(f"Saved private key '{method_fragment}' to {private_key_path}")

    # Save DID document
    with open(did_path, "w", encoding="utf-8") as f:
        json.dump(did_document, f, indent=2)
    logging.info(f"Saved DID document to {did_path}")

    return did_document, keys, str(user_dir)


async def send_authenticated_request(
    target_url: str,
    auth_client: DIDWbaAuthHeader,
    method: str = "GET",
    json_data: Optional[Dict] = None,
) -> Tuple[int, Dict[str, Any], Optional[str]]:
    """
    Send request with DID WBA authentication.

    Args:
        target_url: Target URL
        auth_client: DID WBA authentication client
        method: HTTP method
        json_data: Optional JSON data

    Returns:
        Tuple[int, Dict[str, Any], Optional[str]]: Status code, response, and token
    """
    try:
        # Get authentication headers
        auth_headers = auth_client.get_auth_header(target_url)

        logging.info(
            f"Sending authenticated request to {target_url} with headers: {auth_headers}"
        )

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(target_url, headers=auth_headers) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    # x = dict(response.headers)
                    token = auth_client.update_token(target_url, dict(response.headers))
                    # token = auth_client.update_token(target_url, response_data )
                    return status, response_data, token
            elif method.upper() == "POST":
                async with session.post(
                    target_url, headers=auth_headers, json=json_data
                ) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    token = auth_client.update_token(target_url, dict(response.headers))
                    return status, response_data, token
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return 400, {"error": "Unsupported HTTP method"}, None
    except Exception as e:
        logging.error(f"Error sending authenticated request: {e}", exc_info=True)
        return 500, {"error": str(e)}, None


async def send_request_with_token(
    target_url: str, token: str, method: str = "GET", json_data: Optional[Dict] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Send request using acquired token.

    Args:
        target_url: Target URL
        token: Access token
        method: HTTP method
        json_data: Optional JSON data

    Returns:
        Tuple[int, Dict[str, Any]]: Status code and response
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(target_url, headers=headers) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    return status, response_data
            elif method.upper() == "POST":
                async with session.post(
                    target_url, headers=headers, json=json_data
                ) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    return status, response_data
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return 400, {"error": "Unsupported HTTP method"}
    except Exception as e:
        logging.error(f"Error sending request with token: {e}")
        return 500, {"error": str(e)}
