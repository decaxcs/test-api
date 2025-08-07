#!/usr/bin/env python3
"""
Example: Fetching Mass Messages with UltimaScraperAPI
This example demonstrates how to fetch mass messages (promotional messages sent to multiple users).
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


async def fetch_mass_messages_example():
    """
    Example of fetching mass messages from a specific user.
    Mass messages are promotional messages sent to multiple subscribers.
    """
    logger.info("Starting mass message fetching example")
    
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
        
        # Get a user to fetch mass messages from
        username = input("Enter username to fetch mass messages from: ").strip()
        if not username:
            username = "example_user"  # Default for testing
        
        logger.info(f"Fetching user: {username}")
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Fetch mass messages
        logger.info("Fetching mass messages...")
        
        # Basic mass message fetching
        mass_messages = await user.get_mass_messages()
        
        logger.info(f"✓ Fetched {len(mass_messages)} mass messages")
        
        # Display mass messages
        if mass_messages:
            print(f"\n=== Mass Messages from {user.username} ===")
            for i, message in enumerate(mass_messages, 1):
                print(f"\n--- Mass Message {i} ---")
                print(f"ID: {message.id}")
                print(f"From: {message.get_author().username}")
                print(f"Date: {message.created_at}")
                print(f"Text: {message.text[:100]}..." if len(message.text) > 100 else f"Text: {message.text}")
                print(f"Price: ${message.price/100 if message.price else 0}")
                print(f"Media Count: {message.media_count or 0}")
                print(f"Is From Queue: {message.is_from_queue}")
                print(f"Queue ID: {message.queue_id}")
                print(f"Can Purchase: {message.canPurchase}")
        else:
            print(f"No mass messages found for user {username}")
        
        # Example: Fetch mass messages with cutoff
        logger.info("\n--- Mass Messages with Cutoff Example ---")
        if mass_messages:
            # Use the first mass message as cutoff point
            cutoff_id = mass_messages[0].id
            cutoff_mass_messages = await user.get_mass_messages(message_cutoff_id=cutoff_id)
            logger.info(f"Mass messages up to cutoff ID {cutoff_id}: {len(cutoff_mass_messages)}")
        
        # Analyze mass messages
        if mass_messages:
            print(f"\n=== Mass Message Analysis ===")
            
            # Count by price
            free_mass = [msg for msg in mass_messages if not msg.price or msg.price == 0]
            paid_mass = [msg for msg in mass_messages if msg.price and msg.price > 0]
            
            print(f"Free mass messages: {len(free_mass)}")
            print(f"Paid mass messages: {len(paid_mass)}")
            
            if paid_mass:
                total_value = sum(msg.price for msg in paid_mass) / 100
                avg_price = total_value / len(paid_mass)
                print(f"Total value of paid mass messages: ${total_value:.2f}")
                print(f"Average price: ${avg_price:.2f}")
            
            # Count by media
            media_mass = [msg for msg in mass_messages if msg.media_count and msg.media_count > 0]
            print(f"Mass messages with media: {len(media_mass)}")
            
            # Show most expensive mass messages
            if paid_mass:
                expensive_messages = sorted(paid_mass, key=lambda x: x.price, reverse=True)[:3]
                print(f"\n=== Most Expensive Mass Messages ===")
                for i, msg in enumerate(expensive_messages, 1):
                    print(f"{i}. ${msg.price/100:.2f} - {msg.text[:50]}..." if len(msg.text) > 50 else f"{i}. ${msg.price/100:.2f} - {msg.text}")
    
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
        logger.exception("Full exception details:")
    
    finally:
        # Clean up
        await api.close_pools()
        logger.info("API connections closed")


async def compare_regular_vs_mass_messages():
    """
    Compare regular messages vs mass messages for analysis.
    """
    logger.info("Starting regular vs mass message comparison")
    
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
        
        username = input("Enter username for message comparison: ").strip()
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        # Fetch both types
        logger.info("Fetching regular messages...")
        regular_messages = await user.get_messages(limit=50)
        
        logger.info("Fetching mass messages...")
        mass_messages = await user.get_mass_messages()
        
        print(f"\n=== Message Comparison for {user.username} ===")
        print(f"Regular messages: {len(regular_messages)}")
        print(f"Mass messages: {len(mass_messages)}")
        
        # Analyze regular messages
        regular_paid = [msg for msg in regular_messages if msg.price and msg.price > 0]
        regular_free = [msg for msg in regular_messages if msg.isFree]
        
        # Analyze mass messages
        mass_paid = [msg for msg in mass_messages if msg.price and msg.price > 0]
        mass_free = [msg for msg in mass_messages if not msg.price or msg.price == 0]
        
        print(f"\n=== Breakdown ===")
        print(f"Regular - Paid: {len(regular_paid)}, Free: {len(regular_free)}")
        print(f"Mass - Paid: {len(mass_paid)}, Free: {len(mass_free)}")
        
        # Calculate spending
        regular_total = sum(msg.price for msg in regular_paid if msg.price) / 100
        mass_total = sum(msg.price for msg in mass_paid if msg.price) / 100
        
        print(f"\n=== Spending Analysis ===")
        print(f"Spent on regular messages: ${regular_total:.2f}")
        print(f"Spent on mass messages: ${mass_total:.2f}")
        print(f"Total spent: ${regular_total + mass_total:.2f}")
        
        # Show recent activity
        all_messages = regular_messages + mass_messages
        all_messages.sort(key=lambda x: x.created_at, reverse=True)
        
        print(f"\n=== Recent Activity (All Messages) ===")
        for msg in all_messages[:10]:
            msg_type = "MASS" if hasattr(msg, 'is_from_queue') and msg.is_from_queue else "REGULAR"
            price_str = f"${msg.price/100:.2f}" if msg.price else "FREE"
            print(f"[{msg_type}] {price_str} - {msg.text[:50]}..." if len(msg.text) > 50 else f"[{msg_type}] {price_str} - {msg.text}")
    
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
    
    finally:
        await api.close_pools()


async def mass_message_purchasing_example():
    """
    Example of purchasing mass messages (PPV content).
    WARNING: This will actually spend money if executed!
    """
    logger.warning("WARNING: This example can spend real money!")
    logger.info("Mass message purchasing example")
    
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
        
        username = input("Enter username to check purchasable mass messages: ").strip()
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        # Get mass messages
        mass_messages = await user.get_mass_messages()
        
        # Find purchasable messages
        purchasable = [msg for msg in mass_messages if msg.canPurchase and msg.price and msg.price > 0]
        
        if purchasable:
            print(f"\n=== Purchasable Mass Messages ===")
            for i, msg in enumerate(purchasable[:5], 1):
                print(f"{i}. ${msg.price/100:.2f} - {msg.text[:50]}..." if len(msg.text) > 50 else f"{i}. ${msg.price/100:.2f} - {msg.text}")
            
            print(f"\nFound {len(purchasable)} purchasable mass messages")
            print("To actually purchase, uncomment the buy_message() call in the code")
            print("WARNING: This will spend real money!")
            
            # Uncomment the following lines to actually purchase (AT YOUR OWN RISK!)
            # confirm = input("Type 'YES' to confirm purchase of first message: ")
            # if confirm == "YES" and purchasable:
            #     result = await purchasable[0].buy_message()
            #     logger.info(f"Purchase result: {result}")
        else:
            print("No purchasable mass messages found")
    
    except Exception as e:
        logger.error(f"Purchase example error: {str(e)}")
    
    finally:
        await api.close_pools()


if __name__ == "__main__":
    print("UltimaScraperAPI - Mass Message Fetching Example")
    print("=" * 50)
    
    choice = input(
        "Choose example:\n"
        "1. Basic mass message fetching\n"
        "2. Compare regular vs mass messages\n"
        "3. Mass message purchasing (WARNING: Costs money!)\n"
        "Enter choice (1, 2, or 3): "
    ).strip()
    
    if choice == "2":
        asyncio.run(compare_regular_vs_mass_messages())
    elif choice == "3":
        asyncio.run(mass_message_purchasing_example())
    else:
        asyncio.run(fetch_mass_messages_example())

