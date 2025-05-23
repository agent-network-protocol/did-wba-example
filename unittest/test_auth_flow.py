#!/usr/bin/env python3
"""
Test script to verify the complete DID WBA authentication flow.

This script tests:
1. DID generation
2. DID WBA authentication and token generation
3. Token-based authentication for subsequent requests
"""

import asyncio
import json
import aiohttp
import logging
import secrets
from pathlib import Path

from auth.did_auth import generate_or_load_did, send_authenticated_request, send_request_with_token
from agent_connect.authentication import DIDWbaAuthHeader
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_complete_auth_flow():
    """Test the complete DID WBA authentication flow."""
    
    # Step 1: Generate or load DID
    unique_id = f"test_{secrets.token_hex(4)}"
    logger.info(f"=== Step 1: Generating DID for unique_id: {unique_id} ===")
    
    try:
        did_document, keys, user_dir = await generate_or_load_did(unique_id)
        did_document_path = Path(user_dir) / settings.DID_DOCUMENT_FILENAME
        private_key_path = Path(user_dir) / settings.PRIVATE_KEY_FILENAME
        
        logger.info(f"✓ DID document created: {did_document['id']}")
        logger.info(f"✓ DID document path: {did_document_path}")
        logger.info(f"✓ Private key path: {private_key_path}")
        
        # Verify files exist
        assert did_document_path.exists(), "DID document file should exist"
        assert private_key_path.exists(), "Private key file should exist"
        logger.info("✓ All required files exist")
        
    except Exception as e:
        logger.error(f"✗ Step 1 failed: {e}")
        return False

    # Step 2: DID WBA Authentication
    logger.info(f"\n=== Step 2: Testing DID WBA Authentication ===")
    
    try:
        # Target server information
        target_host = settings.TARGET_SERVER_HOST
        target_port = settings.TARGET_SERVER_PORT
        test_url = f"http://{target_host}:{target_port}/wba/test"
        
        # Create DIDWbaAuthHeader instance
        auth_client = DIDWbaAuthHeader(
            did_document_path=str(did_document_path),
            private_key_path=str(private_key_path)
        )
        
        # Send request with DID WBA authentication
        logger.info(f"Sending authenticated request to {test_url}")
        status, response, token = await send_authenticated_request(test_url, auth_client)
        
        if status != 200:
            logger.error(f"✗ Authentication failed! Status: {status}")
            logger.error(f"Response: {response}")
            return False
            
        logger.info(f"✓ Authentication successful! Status: {status}")
        logger.info(f"✓ Response: {response}")
        logger.info(f"✓ Received token: {token[:50]}..." if token else "✗ No token received")
        
        if not token:
            logger.error("✗ No access token received from server")
            return False
            
    except Exception as e:
        logger.error(f"✗ Step 2 failed: {e}")
        return False

    # Step 3: Token-based Authentication
    logger.info(f"\n=== Step 3: Testing Token-based Authentication ===")
    
    try:
        # Use token for subsequent request
        logger.info("Sending token-based request")
        status, response = await send_request_with_token(test_url, token)
        
        if status != 200:
            logger.error(f"✗ Token authentication failed! Status: {status}")
            logger.error(f"Response: {response}")
            return False
            
        logger.info(f"✓ Token authentication successful! Status: {status}")
        logger.info(f"✓ Response: {response}")
        
    except Exception as e:
        logger.error(f"✗ Step 3 failed: {e}")
        return False

    # Step 4: Additional verification tests
    logger.info(f"\n=== Step 4: Additional Verification Tests ===")
    
    try:
        # Test DID document resolution
        did_url = f"http://{target_host}:{target_port}/wba/user/{unique_id}/did.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(did_url) as resp:
                if resp.status == 200:
                    resolved_did = await resp.json()
                    assert resolved_did['id'] == did_document['id']
                    logger.info(f"✓ DID document resolution successful")
                else:
                    logger.error(f"✗ DID document resolution failed: {resp.status}")
                    return False
        
        # Test root endpoint (should not require authentication)
        root_url = f"http://{target_host}:{target_port}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(root_url) as resp:
                if resp.status == 200:
                    root_response = await resp.json()
                    logger.info(f"✓ Root endpoint accessible: {root_response['service']}")
                else:
                    logger.error(f"✗ Root endpoint failed: {resp.status}")
                    return False
        
    except Exception as e:
        logger.error(f"✗ Step 4 failed: {e}")
        return False

    logger.info(f"\n=== 🎉 All Tests Passed! ===")
    logger.info("The DID WBA authentication flow is working correctly:")
    logger.info("1. ✓ DID generation and storage")
    logger.info("2. ✓ DID WBA signature verification and token generation")
    logger.info("3. ✓ Token-based authentication for subsequent requests")
    logger.info("4. ✓ DID document resolution")
    
    return True


async def main():
    """Main test function."""
    logger.info("Starting DID WBA Authentication Flow Test")
    logger.info(f"Target server: {settings.TARGET_SERVER_HOST}:{settings.TARGET_SERVER_PORT}")
    
    success = await test_complete_auth_flow()
    
    if success:
        logger.info("\n🎉 Test completed successfully!")
        exit(0)
    else:
        logger.error("\n❌ Test failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 