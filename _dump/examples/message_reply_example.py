#!/usr/bin/env python3
"""
Message Reply Example
Demonstrates how to fetch messages and reply to them using the MessageModel.reply() method
"""

import asyncio
import orjson
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def message_reply_example():
    """Example showing how to reply to messages"""
    logger.info("Starting message reply example")
    
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
        
        # Get username to interact with
        username = input("Enter username to view messages from: ").strip()
        if not username:
            logger.error("Username is required!")
            return
            
        user = await authed.get_user(username)
        if not user:
            logger.error(f"User '{username}' not found")
            return
            
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Fetch recent messages
        logger.info("Fetching recent messages...")
        messages = await user.get_messages(limit=10)
        
        if not messages:
            logger.info("No messages found with this user")
            
            # Offer to send a new message
            send_new = input("Would you like to send a new message? (y/n): ").strip().lower()
            if send_new == 'y':
                text = input("Enter message text: ").strip()
                if text:
                    result = await user.send_message(text)
                    if result:
                        print(f"✓ Message sent! ID: {result.id}")
                    else:
                        print("❌ Failed to send message")
            return
        
        # Display messages
        print(f"\n=== Recent Messages with {user.username} ===")
        for i, msg in enumerate(messages[:5], 1):
            author_name = msg.get_author().username
            is_from_me = msg.get_author().id == authed.id
            
            print(f"\n{i}. Message ID: {msg.id}")
            print(f"   From: {author_name} {'(You)' if is_from_me else ''}")
            print(f"   Text: {msg.text[:100]}{'...' if len(msg.text) > 100 else ''}")
            print(f"   Price: ${msg.price/100:.2f}" if msg.price else "   Price: Free")
            print(f"   Media count: {msg.media_count or 0}")
            print(f"   Created: {msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ask which message to reply to
        print("\nWhich message would you like to reply to?")
        choice = input("Enter message number (1-5) or 'n' for new message: ").strip()
        
        if choice.lower() == 'n':
            # Send new message
            text = input("Enter message text: ").strip()
            if text:
                result = await user.send_message(text)
                if result:
                    print(f"✓ New message sent! ID: {result.id}")
                else:
                    print("❌ Failed to send message")
        elif choice.isdigit() and 1 <= int(choice) <= min(5, len(messages)):
            # Reply to selected message
            selected_msg = messages[int(choice) - 1]
            
            print(f"\nReplying to message from {selected_msg.get_author().username}")
            reply_text = input("Enter your reply: ").strip()
            
            if reply_text:
                # Ask about pricing
                is_paid = input("Make this a paid reply? (y/n): ").strip().lower() == 'y'
                price = 0
                if is_paid:
                    price_dollars = float(input("Enter price in dollars (e.g., 5.99): ").strip())
                    price = int(price_dollars * 100)  # Convert to cents
                
                # Send the reply
                logger.info(f"Sending {'paid' if price > 0 else 'free'} reply...")
                result = await selected_msg.reply(reply_text, price=price)
                
                if result:
                    print(f"\n✓ Reply sent successfully!")
                    print(f"Reply ID: {result.id}")
                    print(f"Text: {result.text}")
                    if price > 0:
                        print(f"Price: ${price/100:.2f}")
                else:
                    print("❌ Failed to send reply")
        else:
            print("Invalid choice")
            
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.exception("Full error:")
        
    finally:
        await api.close_pools()
        logger.info("API connections closed")


async def conversation_example():
    """Example showing a back-and-forth conversation"""
    logger.info("Starting conversation example")
    
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
        username = input("Enter username to chat with: ").strip()
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
            
        print(f"\n✓ Connected to {user.username}")
        print("Type 'exit' to end conversation")
        print("-" * 50)
        
        while True:
            # Get message from user
            text = input("\nYou: ").strip()
            
            if text.lower() == 'exit':
                break
                
            if text:
                # Send message
                result = await user.send_message(text)
                if result:
                    print(f"✓ Sent (ID: {result.id})")
                    
                    # Wait a moment and check for new messages
                    await asyncio.sleep(2)
                    
                    # Fetch latest messages to see if there's a reply
                    messages = await user.get_messages(limit=5)
                    for msg in messages:
                        if msg.id > result.id and msg.get_author().id == user.id:
                            print(f"\n{user.username}: {msg.text}")
                            break
                else:
                    print("❌ Failed to send message")
                    
    finally:
        await api.close_pools()


if __name__ == "__main__":
    print("OnlyFans Message Reply Example")
    print("=" * 50)
    print("\nThis example demonstrates:")
    print("1. Fetching messages from a user")
    print("2. Replying to specific messages")
    print("3. Sending new messages")
    print("4. Creating paid replies")
    print()
    
    mode = input("Choose mode: (1) Reply to messages, (2) Conversation mode: ").strip()
    
    if mode == "2":
        asyncio.run(conversation_example())
    else:
        asyncio.run(message_reply_example())