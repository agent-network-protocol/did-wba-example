"""
广告数据 API 路由.
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Request, Header, HTTPException

router = APIRouter(tags=["advertisement"])


@router.get("/ad.json", summary="获取广告数据")
async def get_ad_data(request: Request) -> Dict:
    """
    获取广告数据。此端点需要认证。
    用户数据由身份验证中间件自动添加到 request.state。

    Args:
        request: FastAPI 请求对象

    Returns:
        Dict: 广告数据
    """
    # 用户已经通过中间件认证
    # 中间件将用户数据添加到 request.state.user
    user = request.state.user

    if not user:
        # 这种情况不应该发生，因为中间件应该捕获这种情况
        raise HTTPException(status_code=401, detail="Authentication required")

    # 记录访问
    logging.info(f"Advertisement data accessed by DID: {user.get('did')}")

    # 返回广告数据
    return {
        "id": "123456",
        "name": "示例广告",
        "description": "这是一个示例广告数据，需要 DID WBA 认证才能访问",
        "created_by": user.get("did"),
        "timestamp": "2025-04-21T00:00:00Z",
        "content": {
            "title": "示例产品",
            "price": 99.99,
            "currency": "CNY",
            "available": True,
            "tags": ["sample", "product", "did-wba"],
        },
    }
