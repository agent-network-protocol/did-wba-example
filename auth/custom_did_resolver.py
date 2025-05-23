"""
自定义DID文档解析器，用于本地测试环境
"""

import os
import json
import logging
import aiohttp
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import unquote, urlparse


async def resolve_local_did_document(did: str) -> Optional[Dict]:
    """
    解析本地DID文档

    Args:
        did: DID标识符，例如did:wba:localhost%3A8000:wba:user:123456

    Returns:
        Optional[Dict]: 解析出的DID文档，如果解析失败则返回None
    """
    try:
        logging.info(f"解析本地DID文档: {did}")

        # 解析DID标识符
        parts = did.split(":")
        if len(parts) < 5 or parts[0] != "did" or parts[1] != "wba":
            logging.error(f"无效的DID格式: {did}")
            return None

        # 提取主机名、端口和用户ID
        hostname = parts[2]
        # 解码端口部分，如果存在
        if "%3A" in hostname:
            hostname = unquote(hostname)  # 将 %3A 解码为 :

        path_segments = parts[3:]
        user_id = path_segments[-1]

        logging.info(f"DID 解析结果 - 主机名: {hostname}, 用户ID: {user_id}")

        # 查找本地文件系统中的DID文档
        current_dir = Path(__file__).parent.parent.absolute()
        did_path = current_dir / "did_keys" / f"user_{user_id}" / "did.json"

        if did_path.exists():
            logging.info(f"找到本地DID文档: {did_path}")
            with open(did_path, "r", encoding="utf-8") as f:
                did_document = json.load(f)
            return did_document

        # 如果本地未找到，尝试通过HTTP请求获取
        http_url = f"http://{hostname}/wba/user/{user_id}/did.json"
        logging.info(f"尝试通过HTTP获取DID文档: {http_url}")

        # 这里使用异步HTTP请求
        async with aiohttp.ClientSession() as session:
            async with session.get(http_url, ssl=False) as response:
                if response.status == 200:
                    did_document = await response.json()
                    logging.info("成功通过HTTP获取DID文档")
                    return did_document
                else:
                    logging.error(f"HTTP请求失败，状态码: {response.status}")
                    return None

    except Exception as e:
        logging.error(f"解析DID文档时出错: {e}")
        return None
