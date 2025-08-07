#!/usr/bin/env python3
"""
Send Message Function for OnlyFans API
This adds the ability to send messages to users
"""

import asyncio
import orjson
from pathlib import Path
from datetime import datetime
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from logging_config import setup_logging, get_logger
import time

# Setup logging with debug level
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def send_message(user_model, recipient_id: int, text: str, price: int = 0, media_ids: list[int] = None):
    """
    Send a message to a user
    
    Args:
        user_model: The authenticated user model
        recipient_id: The user ID to send message to
        text: The message text
        price: Price in cents (0 for free message)
        media_ids: List of media IDs to attach (optional)
    
    Returns:
        dict: Response from the API
    """
    # Build the endpoint URL
    endpoint = f"https://onlyfans.com/api2/v2/chats/{recipient_id}/messages"
    
    # Build the payload
    payload = {
        "text": text,
        "lockedText": False,
        "mediaFiles": media_ids or [],
        "price": price,  # Price in cents (0 = free)
        "isCouplePeopleMedia": False,
        "isForward": False
    }
    
    logger.info(f"Sending message to user {recipient_id}")
    logger.debug(f"Payload: {payload}")
    
    try:
        # Make the POST request using the existing session manager
        response = await user_model.get_requester().json_request(
            endpoint,
            method="POST",
            payload=payload
        )
        
        if response and isinstance(response, dict):
            logger.info(f"✓ Message sent successfully! Message ID: {response.get('id')}")
            return response
        else:
            logger.error(f"Failed to send message. Response: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Error sending message: {type(e).__name__}: {str(e)}")
        raise


# Add this method to the UserModel class
async def send_message_to_user(self, text: str, price: int = 0, media_ids: list[int] = None):
    """
    Send a message to this user
    
    Args:
        text: The message text
        price: Price in cents (0 for free message)
        media_ids: List of media IDs to attach (optional)
    
    Returns:
        dict: Message response
    """
    return await send_message(self.get_authed(), self.id, text, price, media_ids)


async def example_usage():
    """Example of how to use the send message function"""
    logger.info("Starting send message example")
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load authentication
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json file not found!")
            return
            
        auth_json = orjson.loads(auth_path.read_bytes())
        logger.info("Loaded authentication")
        
        # Authenticate
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
            
        logger.info("✓ Authentication successful")
        
        # Get the user to send message to
        username = input("Enter username to send message to: ").strip()
        if not username:
            logger.error("Username is required!")
            return
            
        user = await authed.get_user(username)
        if not user:
            logger.error(f"User '{username}' not found")
            return
            
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Get message details
        message_text = input("Enter message text: ").strip()
        if not message_text:
            logger.error("Message text is required!")
            return
            
        # Ask about pricing
        is_paid = input("Is this a paid message? (y/n): ").strip().lower() == 'y'
        price = 0
        if is_paid:
            price_dollars = float(input("Enter price in dollars (e.g., 5.99): ").strip())
            price = int(price_dollars * 100)  # Convert to cents
            
        # Send the message
        logger.info(f"Sending {'paid' if price > 0 else 'free'} message...")
        
        result = await send_message(authed, user.id, message_text, price)
        
        if result:
            print(f"\n✓ Message sent successfully!")
            print(f"Message ID: {result.get('id')}")
            print(f"Text: {result.get('text')}")
            print(f"Price: ${result.get('price', 0) / 100:.2f}")
            print(f"Created at: {result.get('createdAt')}")
        else:
            print("❌ Failed to send message")
            
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.exception("Full error:")
        
    finally:
        await api.close_pools()
        logger.info("API connections closed")


async def simple_send_message_example():
    """Simplified example using the built-in send_message method"""
    logger.info("Starting simple send message example")
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load and authenticate
        auth_json = orjson.loads(Path("auth.json").read_bytes())
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
            
        # Get user
        username = input("Enter username to send message to: ").strip()
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
            
        # Send message using the built-in method
        message_text = input("Enter message text: ").strip()
        
        # Send free message
        result = await user.send_message(message_text)
        
        # Or send paid message
        # result = await user.send_message(message_text, price=500)  # $5.00
        
        # Or send with media
        # result = await user.send_message(message_text, media_ids=[12345, 67890])
        
        if result:
            print(f"\n✓ Message sent successfully!")
            print(f"Message ID: {result.id}")
            print(f"Text: {result.text}")
        else:
            print("❌ Failed to send message")
            
    finally:
        await api.close_pools()


if __name__ == "__main__":
    print("OnlyFans Send Message Example")
    print("=" * 50)
    print("\nNote: The send_message method is now built into UserModel!")
    print("You can use it like: await user.send_message('Hello!')")
    print()
    
    # Run the example
    asyncio.run(simple_send_message_example())