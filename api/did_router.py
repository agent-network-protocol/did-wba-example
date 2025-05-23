"""
DID document API router.
"""

import json
import logging
from typing import Dict
from pathlib import Path
from fastapi import APIRouter, HTTPException

from core.config import settings

router = APIRouter(tags=["did"])


@router.get("/wba/user/{user_id}/did.json", summary="Get DID document")
async def get_did_document(user_id: str) -> Dict:
    """
    Retrieve a DID document by user ID.

    Args:
        user_id: User identifier

    Returns:
        Dict: DID document
    """
    # 构建DID文档路径
    current_dir = Path(__file__).parent.parent.absolute()
    did_path = (
        current_dir
        / settings.DID_DOCUMENTS_PATH
        / f"user_{user_id}"
        / settings.DID_DOCUMENT_FILENAME
    )

    if not did_path.exists():
        raise HTTPException(
            status_code=404, detail=f"DID document not found for user {user_id}"
        )

    # 加载DID文档
    try:
        with open(did_path, "r", encoding="utf-8") as f:
            did_document = json.load(f)
        return did_document
    except Exception as e:
        logging.error(f"Error loading DID document: {e}")
        raise HTTPException(status_code=500, detail="Error loading DID document")


@router.put("/wba/user/{user_id}/did.json", summary="Store DID document")
async def store_did_document(user_id: str, did_document: Dict) -> Dict:
    """
    Store a DID document for a user.

    Args:
        user_id: User identifier
        did_document: DID document to store

    Returns:
        Dict: Operation result
    """
    # 构建存储路径
    current_dir = Path(__file__).parent.parent.absolute()
    user_dir = current_dir / settings.DID_DOCUMENTS_PATH / f"user_{user_id}"
    did_path = user_dir / settings.DID_DOCUMENT_FILENAME

    # 创建目录（如果不存在）
    user_dir.mkdir(parents=True, exist_ok=True)

    # 保存DID文档
    try:
        with open(did_path, "w", encoding="utf-8") as f:
            json.dump(did_document, f, indent=2)

        return {
            "status": "success",
            "message": f"DID document stored for user {user_id}",
            "path": str(did_path),
        }
    except Exception as e:
        logging.error(f"Error storing DID document: {e}")
        raise HTTPException(status_code=500, detail="Error storing DID document")


@router.get("/agents/example/ad.json", summary="Get agent description")
async def get_agent_description() -> Dict:
    """
    Get agent description document.

    Returns:
        Dict: Agent description
    """
    return {
        "id": "example-agent-123",
        "name": "DID WBA Example Agent",
        "description": "An example agent implementing DID WBA authentication",
        "version": "0.1.0",
        "capabilities": ["did-wba-authentication", "token-authentication"],
        "endpoints": {
            "auth": "/auth/did-wba",
            "verify": "/auth/verify",
            "test": "/wba/test",
        },
        "owner": "DID WBA Example",
        "created_at": "2025-04-21T00:00:00Z",
    }
