#!/usr/bin/env python3
"""
Fetch All Messages and Save to JSON
This script fetches all messages from a specific OnlyFans user and saves them to a JSON file.
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


async def fetch_all_messages_to_json():
    """
    Fetches all messages from a user and saves them to a JSON file.
    """
    logger.info("Starting fetch all messages to JSON")
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    try:
        # Load authentication from auth.json
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json file not found! Please create it first.")
            return
        
        auth_json = orjson.loads(auth_path.read_bytes())
        logger.info("Loaded authentication from auth.json")
        
        # Authenticate
        authed = await api.login(auth_json["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
        
        logger.info("✓ Authentication successful")
        
        # Get username to fetch messages from
        username = input("Enter username to fetch all messages from: ").strip()
        if not username:
            logger.error("Username is required!")
            return
        
        logger.info(f"Fetching user: {username}")
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Fetch all messages with pagination
        logger.info("Starting to fetch all messages...")
        all_messages = []
        seen_message_ids = set()  # Track seen messages to avoid duplicates
        limit = 100  # Max messages per request
        offset_id = None
        page = 1
        consecutive_duplicate_pages = 0
        
        while True:
            logger.info(f"Fetching page {page} (limit: {limit}, offset_id: {offset_id})...")
            
            try:
                page_messages = await user.get_messages(limit=limit, offset_id=offset_id)
                
                if not page_messages:
                    logger.info("No more messages found")
                    break
                
                # Filter out duplicates
                new_messages = []
                for msg in page_messages:
                    if msg.id not in seen_message_ids:
                        new_messages.append(msg)
                        seen_message_ids.add(msg.id)
                
                if not new_messages:
                    consecutive_duplicate_pages += 1
                    logger.warning(f"Page {page}: All messages were duplicates")
                    
                    # If we get 3 pages of only duplicates, we've likely reached the end
                    if consecutive_duplicate_pages >= 3:
                        logger.info("Reached end of messages (multiple duplicate pages)")
                        break
                else:
                    consecutive_duplicate_pages = 0
                    all_messages.extend(new_messages)
                    logger.info(f"✓ Page {page}: fetched {len(new_messages)} new messages (total: {len(all_messages)})")
                
                # Set offset for next page using the last message ID from the original page
                if page_messages:
                    offset_id = page_messages[-1].id
                else:
                    break
                    
                page += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                break
        
        logger.info(f"\n✓ Finished fetching! Total messages: {len(all_messages)}")
        
        # Convert messages to JSON-serializable format
        logger.info("Converting messages to JSON format...")
        messages_data = []
        
        for msg in all_messages:
            message_dict = {
                "id": msg.id,
                "text": msg.text,
                "price": msg.price,
                "price_dollars": msg.price / 100 if msg.price else 0,
                "is_free": msg.isFree,
                "is_tip": msg.isTip,
                "is_opened": msg.isOpened,
                "is_new": msg.isNew,
                "is_from_queue": msg.is_from_queue,
                "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') and msg.created_at else None,
                "changed_at": msg.changedAt if hasattr(msg, 'changedAt') and msg.changedAt else None,
                "media_count": msg.media_count or 0,
                "preview_count": len(msg.previews) if hasattr(msg, 'previews') else 0,
                "is_liked": msg.isLiked,
                "is_media_ready": msg.isMediaReady,
                "can_purchase": msg.canPurchase,
                "locked_text": msg.lockedText,
                "response_type": msg.responseType if hasattr(msg, 'responseType') else None,
                "author": {
                    "id": msg.get_author().id,
                    "username": msg.get_author().username,
                    "name": msg.get_author().name,
                },
            }
            
            # Add media information if available
            if hasattr(msg, 'media') and msg.media:
                message_dict["media"] = []
                for media_item in msg.media:
                    media_info = {
                        "id": getattr(media_item, 'id', None),
                        "type": getattr(media_item, 'type', None),
                        "can_view": getattr(media_item, 'canView', None),
                        "has_error": getattr(media_item, 'hasError', None),
                    }
                    message_dict["media"].append(media_info)
            
            messages_data.append(message_dict)
        
        # Sort messages by date (newest first)
        messages_data.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"messages_{username}_{timestamp}.json"
        output_path = Path(output_filename)
        
        # Save to JSON file
        logger.info(f"Saving to {output_filename}...")
        output_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
            },
            "fetch_date": datetime.now().isoformat(),
            "total_messages": len(messages_data),
            "messages": messages_data
        }
        
        # Write with pretty formatting
        with open(output_path, 'wb') as f:
            f.write(orjson.dumps(output_data, option=orjson.OPT_INDENT_2))
        
        logger.info(f"✓ Successfully saved {len(messages_data)} messages to {output_filename}")
        
        # Print summary statistics
        print(f"\n=== Message Statistics for {user.username} ===")
        print(f"Total messages: {len(messages_data)}")
        
        paid_count = sum(1 for msg in messages_data if msg['price'] and msg['price'] > 0)
        free_count = sum(1 for msg in messages_data if msg['is_free'])
        tip_count = sum(1 for msg in messages_data if msg['is_tip'])
        media_count = sum(1 for msg in messages_data if msg['media_count'] > 0)
        total_spent = sum(msg['price_dollars'] for msg in messages_data if msg['price'])
        
        print(f"Paid messages: {paid_count}")
        print(f"Free messages: {free_count}")
        print(f"Tip messages: {tip_count}")
        print(f"Messages with media: {media_count}")
        print(f"Total spent: ${total_spent:.2f}")
        
        if messages_data:
            # Find date range
            dates = [msg['created_at'] for msg in messages_data if msg['created_at']]
            if dates:
                oldest_date = min(dates)
                newest_date = max(dates)
                print(f"\nDate range: {oldest_date[:10]} to {newest_date[:10]}")
        
        print(f"\n✓ Data saved to: {output_path.absolute()}")
        
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
        logger.exception("Full exception details:")
    
    finally:
        # Clean up
        await api.close_pools()
        logger.info("API connections closed")


if __name__ == "__main__":
    print("UltimaScraperAPI - Fetch All Messages to JSON")
    print("=" * 50)
    print("This script will fetch ALL messages from a user and save them to a JSON file.")
    print("Note: This may take a while for users with many messages.")
    print()
    
    asyncio.run(fetch_all_messages_to_json())