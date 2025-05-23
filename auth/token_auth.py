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
    expires = datetime.utcnow() + (
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
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {"did": payload["sub"], "keyid": payload.get("keyid")}

    except jwt.PyJWTError as e:
        logging.error(f"JWT token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Error during token authentication: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")
