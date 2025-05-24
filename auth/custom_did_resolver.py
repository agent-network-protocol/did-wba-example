"""
Custom DID document resolver for local testing environment.
"""

import json
import logging
import aiohttp
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import unquote


async def resolve_local_did_document(did: str) -> Optional[Dict]:
    """
    Resolve local DID document.

    Args:
        did: DID identifier, e.g., did:wba:localhost%3A8000:wba:user:123456

    Returns:
        Optional[Dict]: Resolved DID document, or None if resolution fails
    """
    try:
        logging.info(f"Resolving local DID document: {did}")

        # Parse DID identifier
        parts = did.split(":")
        if len(parts) < 5 or parts[0] != "did" or parts[1] != "wba":
            logging.error(f"Invalid DID format: {did}")
            return None

        # Extract hostname, port and user ID
        hostname = parts[2]
        # Decode port part if present
        if "%3A" in hostname:
            hostname = unquote(hostname)  # Decode %3A to :

        path_segments = parts[3:]
        user_id = path_segments[-1]

        logging.info(f"DID resolution result - hostname: {hostname}, user ID: {user_id}")

        # Search for DID document in local filesystem
        current_dir = Path(__file__).parent.parent.absolute()
        did_path = current_dir / "did_keys" / f"user_{user_id}" / "did.json"

        if did_path.exists():
            logging.info(f"Found local DID document: {did_path}")
            with open(did_path, "r", encoding="utf-8") as f:
                did_document = json.load(f)
            return did_document

        # If not found locally, try to get via HTTP request
        http_url = f"http://{hostname}/wba/user/{user_id}/did.json"
        logging.info(f"Attempting to fetch DID document via HTTP: {http_url}")

        # Use async HTTP request here
        async with aiohttp.ClientSession() as session:
            async with session.get(http_url, ssl=False) as response:
                if response.status == 200:
                    did_document = await response.json()
                    logging.info("Successfully fetched DID document via HTTP")
                    return did_document
                else:
                    logging.error(f"HTTP request failed, status code: {response.status}")
                    return None

    except Exception as e:
        logging.error(f"Error resolving DID document: {e}")
        return None
