#!/usr/bin/env python3
"""
Simple test for send message with enhanced logging
"""

import asyncio
import json
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_send():
    logger.info("Starting send message test")
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load authentication
        with open("auth.json", "r") as f:
            auth_json = json.load(f)
        
        logger.info("Loaded authentication")
        
        # Authenticate
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
            
        logger.info("✓ Authentication successful")
        
        # Get user
        username = "heyitsmilliexx"
        logger.info(f"Getting user: {username}")
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
            
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Send simple message
        message_text = "goodnight imma sleep"
        logger.info(f"Sending message: '{message_text}'")
        
        try:
            result = await user.send_message(message_text)
            
            if result:
                logger.info(f"✓ Message sent successfully!")
                logger.info(f"Message ID: {result.id}")
                logger.info(f"Text: {result.text}")
                print(f"\n✓ SUCCESS! Message sent with ID: {result.id}")
            else:
                logger.error("Failed to send message - no result returned")
                print("\n❌ FAILED - No result returned")
                
        except Exception as e:
            logger.error(f"Error sending message: {type(e).__name__}: {str(e)}")
            logger.exception("Full traceback:")
            print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
            
    except Exception as e:
        logger.error(f"General error: {type(e).__name__}: {str(e)}")
        logger.exception("Full error:")
        
    finally:
        await api.close_pools()
        logger.info("API connections closed")


if __name__ == "__main__":
    print("Testing send message with enhanced logging...")
    print("=" * 50)
    asyncio.run(test_send())