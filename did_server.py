"""
DID WBA Example with both Client and Server capabilities.
"""

import threading
import time

import logging
import uvicorn
import asyncio
import secrets
import argparse
from pathlib import Path

from core.config import settings
from core.app import create_app
from auth.did_auth import (
    generate_or_load_did,
    send_authenticated_request,
    send_request_with_token,
    DIDWbaAuthHeader,
)
from utils.log_base import set_log_color_level

# Create FastAPI application
app = create_app()


@app.get("/", tags=["status"])
async def root():
    """
    Root endpoint for server status check.

    Returns:
        dict: Server status information
    """
    return {
        "status": "running",
        "service": "DID WBA Example",
        "version": "0.1.0",
        "mode": "Client and Server",
        "documentation": "/docs",
    }


async def client_example(unique_id: str = None):
    """
    Run the client example to demonstrate DID WBA authentication.

    Args:
        unique_id: Optional unique identifier
    """
    try:
        # 1. Generate or load DID document
        if not unique_id:
            unique_id = secrets.token_hex(8)

        logging.info(f"Using unique ID: {unique_id}")
        did_document, keys, user_dir = await generate_or_load_did(unique_id)
        did_document_path = Path(user_dir) / settings.DID_DOCUMENT_FILENAME
        private_key_path = Path(user_dir) / settings.PRIVATE_KEY_FILENAME

        logging.info(f"DID document path: {did_document_path}")
        logging.info(f"Private key path: {private_key_path}")

        # 2. Target server information
        target_host = settings.TARGET_SERVER_HOST
        target_port = settings.TARGET_SERVER_PORT
        base_url = f"http://{target_host}:{target_port}"
        test_url = f"{base_url}/wba/test"

        # 3. Create DIDWbaAuthHeader instance
        auth_client = DIDWbaAuthHeader(
            did_document_path=str(did_document_path),
            private_key_path=str(private_key_path),
        )

        # 4. Send request with DID WBA authentication
        logging.info(f"Sending authenticated request to {test_url}")
        status, response, token = await send_authenticated_request(
            test_url, auth_client
        )

        if status != 200:
            logging.error(f"Authentication failed! Status: {status}")
            logging.error(f"Response: {response}")
            return

        logging.info(f"Authentication successful! Response: {response}")

        # 5. If we received a token, use it for subsequent requests
        if token:
            logging.info("Received access token, trying to use it for next request")
            status, response = await send_request_with_token(test_url, token)

            if status == 200:
                logging.info(f"Token authentication successful! Response: {response}")
            else:
                logging.error(f"Token authentication failed! Status: {status}")
                logging.error(f"Response: {response}")
        else:
            logging.warning("No token received from server")

    except Exception as e:
        logging.error(f"Error in client example: {e}")


if __name__ == "__main__":
    set_log_color_level(logging.INFO)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="DID WBA Example with Client and Server capabilities"
    )
    parser.add_argument("--client", action="store_true", help="Run client example")
    parser.add_argument(
        "--unique-id", type=str, help="Unique ID for client example", default=None
    )
    parser.add_argument(
        "--port",
        type=int,
        help=f"Server port (default: {settings.LOCAL_PORT})",
        default=settings.LOCAL_PORT,
    )

    args = parser.parse_args()
    client_args = args  # Save to global variable for startup event use

    if args.port != settings.LOCAL_PORT:
        settings.LOCAL_PORT = args.port

    # If client mode is enabled, run client example in a separate thread
    if args.client:

        def run_client():
            # Wait 2 seconds to ensure server is started
            time.sleep(2)
            # Create event loop in new thread to run client example
            asyncio.run(client_example(args.unique_id))

        thread = threading.Thread(target=run_client, daemon=True)
        thread.start()
        logging.info("Client thread started, will execute in 2 seconds")

    logging.info(
        f"Starting DID WBA Server on {settings.LOCAL_HOST}:{settings.LOCAL_PORT}"
    )

    # Run server
    uvicorn.run(
        "did_server:app",
        host=settings.LOCAL_HOST,
        port=settings.LOCAL_PORT,
        reload=settings.DEBUG,
    )
