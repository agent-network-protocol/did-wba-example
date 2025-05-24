"""
Bearer token authentication module.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException

from core.config import settings
from auth.jwt_keys import get_jwt_public_key, get_jwt_private_key


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    # Add issued at time (iat)
    now = datetime.utcnow()
    to_encode.update({"iat": now})
    
    # Add expiration time (exp)
    expires = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expires})

    # Get private key for signing
    private_key = get_jwt_private_key()
    if not private_key:
        logging.error("Failed to load JWT private key")
        raise HTTPException(
            status_code=500, detail="Internal server error during token generation"
        )

    # Create the JWT token using RS256 algorithm with private key
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def handle_bearer_auth(token: str) -> Dict:
    """
    Handle Bearer token authentication.

    Args:
        token: JWT token string

    Returns:
        Dict: Token payload with DID information

    Raises:
        HTTPException: When token is invalid
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Get public key for verification
        public_key = get_jwt_public_key()
        if not public_key:
            logging.error("Failed to load JWT public key")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during token verification",
            )

        # Decode and verify the token using the public key
        payload = jwt.decode(token, public_key, algorithms=[settings.JWT_ALGORITHM])

        # Check if token contains required fields
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload: missing 'sub' field")
            
        if "iat" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload: missing 'iat' field")
            
        if "exp" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload: missing 'exp' field")

        # Validate DID format
        did = payload["sub"]
        if not did.startswith("did:wba:"):
            raise HTTPException(status_code=401, detail="Invalid DID format")

        # Additional time validation (JWT library already validates exp)
        now = datetime.utcnow()
        iat = datetime.utcfromtimestamp(payload["iat"])
        exp = datetime.utcfromtimestamp(payload["exp"])
        
        # Allow a small tolerance for clock skew (5 seconds)
        tolerance = timedelta(seconds=5)
        
        # Check if token was issued too far in the future (invalid)
        if iat > now + tolerance:
            raise HTTPException(status_code=401, detail="Token issued in the future")
            
        # Check if token is already expired (redundant check, but explicit)
        if exp <= now - tolerance:
            raise HTTPException(status_code=401, detail="Token has expired")

        return {"did": payload["sub"]}

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except jwt.ExpiredSignatureError:
        logging.error("JWT token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logging.error(f"JWT token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Error during token authentication: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")
