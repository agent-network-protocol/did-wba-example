"""
Advertisement data API router.
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Request, Header, HTTPException

router = APIRouter(tags=["advertisement"])


@router.get("/ad.json", summary="Get advertisement data")
async def get_ad_data(request: Request) -> Dict:
    """
    Get advertisement data. This endpoint requires authentication.
    User data is automatically added to request.state by authentication middleware.

    Args:
        request: FastAPI request object

    Returns:
        Dict: Advertisement data
    """
    # User is already authenticated by middleware
    # Middleware adds user data to request.state.user
    user = request.state.user

    if not user:
        # This should not happen as middleware should catch this case
        raise HTTPException(status_code=401, detail="Authentication required")

    # Log access
    logging.info(f"Advertisement data accessed by DID: {user.get('did')}")

    # Return advertisement data
    return {
        "id": "123456",
        "name": "Example Advertisement",
        "description": "This is an example advertisement data that requires DID WBA authentication to access",
        "created_by": user.get("did"),
        "timestamp": "2025-04-21T00:00:00Z",
        "content": {
            "title": "Example Product",
            "price": 99.99,
            "currency": "USD",
            "available": True,
            "tags": ["sample", "product", "did-wba"],
        },
    }
