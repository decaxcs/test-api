#!/usr/bin/env python3
"""
Example: Fetching Messages with UltimaScraperAPI
This example demonstrates how to fetch messages from OnlyFans users.
"""

import asyncio
import orjson
from pathlib import Path
from datetime import datetime
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def fetch_messages_example():
    """
    Example of fetching messages from a specific user.
    Requires authentication via auth.json file.
    """
    logger.info("Starting message fetching example")
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load authentication from auth.json
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json file not found! Please create it first.")
            logger.info("See the guide for how to create auth.json")
            return
        
        auth_json = orjson.loads(auth_path.read_bytes())
        logger.info("Loaded authentication from auth.json")
        
        # Authenticate
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
        
        logger.info("✓ Authentication successful")
        
        # Get a user to fetch messages from
        # Replace with actual username you want to fetch messages from
        username = input("Enter username to fetch messages from: ").strip()
        if not username:
            username = "heyitsmilliexx"  # Default for testing
        
        logger.info(f"Fetching user: {username}")
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Fetch messages
        logger.info("Fetching messages...")
        
        # Basic message fetching (default: 20 messages)
        messages = await user.get_messages(limit=20)
        
        logger.info(f"✓ Fetched {len(messages)} messages")
        
        # Display messages
        if messages:
            print(f"\n=== Messages from {user.username} ===")
            for i, message in enumerate(messages[:10], 1):  # Show first 10
                print(f"\n--- Message {i} ---")
                print(f"ID: {message.id}")
                print(f"From: {message.get_author().username}")
                print(f"Date: {message.created_at}")
                print(f"Text: {message.text[:100]}..." if len(message.text) > 100 else f"Text: {message.text}")
                print(f"Price: ${message.price/100 if message.price else 0}")
                print(f"Media Count: {message.media_count or 0}")
                print(f"Is Free: {message.isFree}")
                print(f"Is Tip: {message.isTip}")
        else:
            print(f"No messages found for user {username}")
        
        # Example: Fetch messages with pagination
        logger.info("\n--- Pagination Example ---")
        all_messages = []
        limit = 10
        offset_id = None
        page = 1
        
        while page <= 3:  # Fetch first 3 pages
            logger.info(f"Fetching page {page}...")
            page_messages = await user.get_messages(limit=limit, offset_id=offset_id)
            
            if not page_messages:
                logger.info("No more messages")
                break
            
            all_messages.extend(page_messages)
            offset_id = page_messages[-1].id  # Use last message ID as offset
            page += 1
        
        logger.info(f"Total messages fetched with pagination: {len(all_messages)}")
        
        # Example: Fetch messages up to a specific cutoff
        logger.info("\n--- Cutoff Example ---")
        if messages:
            # Use the 5th message as cutoff point
            cutoff_id = messages[4].id if len(messages) > 4 else None
            if cutoff_id:
                cutoff_messages = await user.get_messages(cutoff_id=cutoff_id)
                logger.info(f"Messages up to cutoff ID {cutoff_id}: {len(cutoff_messages)}")
        
        # Example: Get specific message by ID
        logger.info("\n--- Get Message by ID Example ---")
        if messages:
            message_id = messages[0].id
            specific_message = await user.get_message_by_id(
                user_id=user.id, 
                message_id=message_id
            )
            if specific_message:
                logger.info(f"✓ Retrieved specific message: {specific_message.id}")
                print(f"Specific message text: {specific_message.text}")
        
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
        logger.exception("Full exception details:")
    
    finally:
        # Clean up
        await api.close_pools()
        logger.info("API connections closed")


async def fetch_messages_advanced():
    """
    Advanced message fetching with filtering and processing.
    """
    logger.info("Starting advanced message fetching")
    
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load auth
        auth_path = Path("auth.json")
        auth_json = orjson.loads(auth_path.read_bytes())
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
        
        username = input("Enter username for advanced message fetching: ").strip()
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        # Fetch all messages
        logger.info("Fetching all messages...")
        messages = await user.get_messages(limit=100)  # Increase limit
        
        # Filter messages by type
        paid_messages = [msg for msg in messages if msg.price and msg.price > 0]
        free_messages = [msg for msg in messages if msg.isFree]
        tip_messages = [msg for msg in messages if msg.isTip]
        media_messages = [msg for msg in messages if msg.media_count and msg.media_count > 0]
        
        print(f"\n=== Message Statistics for {user.username} ===")
        print(f"Total messages: {len(messages)}")
        print(f"Paid messages: {len(paid_messages)}")
        print(f"Free messages: {len(free_messages)}")
        print(f"Tip messages: {len(tip_messages)}")
        print(f"Messages with media: {len(media_messages)}")
        
        # Calculate total spent on paid messages
        total_spent = sum(msg.price for msg in paid_messages if msg.price) / 100  # Convert cents to dollars
        print(f"Total spent on paid messages: ${total_spent:.2f}")
        
        # Show recent paid messages
        if paid_messages:
            print(f"\n=== Recent Paid Messages ===")
            for msg in paid_messages[:5]:
                print(f"${msg.price/100:.2f} - {msg.text[:50]}..." if len(msg.text) > 50 else f"${msg.price/100:.2f} - {msg.text}")
        
        # Show messages with media
        if media_messages:
            print(f"\n=== Messages with Media ===")
            for msg in media_messages[:5]:
                print(f"Media count: {msg.media_count} - {msg.text[:50]}..." if len(msg.text) > 50 else f"Media count: {msg.media_count} - {msg.text}")
    
    except Exception as e:
        logger.error(f"Advanced fetching error: {str(e)}")
    
    finally:
        await api.close_pools()


if __name__ == "__main__":
    print("UltimaScraperAPI - Message Fetching Example")
    print("=" * 50)
    
    choice = input("Choose example:\n1. Basic message fetching\n2. Advanced message analysis\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(fetch_messages_advanced())
    else:
        asyncio.run(fetch_messages_example())

