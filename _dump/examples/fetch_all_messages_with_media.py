#!/usr/bin/env python3
"""
Fetch All Messages with Enhanced Media Handling
This script fetches all messages from a specific OnlyFans user with proper media information handling.
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


async def fetch_all_messages_with_media():
    """
    Fetches all messages from a user with enhanced media handling.
    """
    logger.info("Starting fetch all messages with media handling")
    
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
        seen_message_ids = set()
        limit = 100
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
                    
                    if consecutive_duplicate_pages >= 3:
                        logger.info("Reached end of messages (multiple duplicate pages)")
                        break
                else:
                    consecutive_duplicate_pages = 0
                    all_messages.extend(new_messages)
                    logger.info(f"✓ Page {page}: fetched {len(new_messages)} new messages (total: {len(all_messages)})")
                
                # Set offset for next page
                if page_messages:
                    offset_id = page_messages[-1].id
                else:
                    break
                    
                page += 1
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                break
        
        logger.info(f"\n✓ Finished fetching! Total messages: {len(all_messages)}")
        
        # Convert messages to JSON-serializable format with enhanced media handling
        logger.info("Converting messages to JSON format with enhanced media handling...")
        messages_data = []
        
        # Track statistics
        locked_media_count = 0
        viewable_media_count = 0
        ppv_messages_count = 0
        
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
            
            # Track PPV messages
            if msg.price and msg.price > 0:
                ppv_messages_count += 1
            
            # Enhanced media information handling
            if hasattr(msg, 'media') and msg.media:
                message_dict["media"] = []
                message_dict["media_status"] = "unknown"
                
                for media_item in msg.media:
                    # Handle both dictionary and object access
                    if isinstance(media_item, dict):
                        media_id = media_item.get('id')
                        media_type = media_item.get('type')
                        can_view = media_item.get('canView')
                        has_error = media_item.get('hasError', False)
                        
                        # Check for additional media attributes
                        source = media_item.get('source')
                        preview = media_item.get('preview')
                        thumb = media_item.get('thumb')
                        is_locked = media_item.get('isLocked', False)
                        
                    else:
                        # Handle object attributes
                        media_id = getattr(media_item, 'id', None)
                        media_type = getattr(media_item, 'type', None)
                        can_view = getattr(media_item, 'canView', None)
                        has_error = getattr(media_item, 'hasError', False)
                        source = getattr(media_item, 'source', None)
                        preview = getattr(media_item, 'preview', None)
                        thumb = getattr(media_item, 'thumb', None)
                        is_locked = getattr(media_item, 'isLocked', False)
                    
                    # Determine media access status
                    if can_view is False or is_locked:
                        media_status = "locked"
                        locked_media_count += 1
                    elif can_view is True:
                        media_status = "viewable"
                        viewable_media_count += 1
                    else:
                        media_status = "unknown"
                    
                    # Try to get URL if available
                    media_url = None
                    if can_view and hasattr(msg, 'url_picker'):
                        try:
                            url_result = msg.url_picker(media_item)
                            if url_result:
                                media_url = url_result.geturl()
                        except:
                            pass
                    
                    media_info = {
                        "id": media_id,
                        "type": media_type,
                        "can_view": can_view,
                        "has_error": has_error,
                        "is_locked": is_locked,
                        "status": media_status,
                        "url": media_url,
                        "preview": preview,
                        "thumb": thumb,
                        "source": source if source and can_view else None,
                    }
                    
                    # Add resolution info if available
                    if isinstance(media_item, dict):
                        if 'width' in media_item:
                            media_info["width"] = media_item.get('width')
                        if 'height' in media_item:
                            media_info["height"] = media_item.get('height')
                        if 'duration' in media_item:
                            media_info["duration"] = media_item.get('duration')
                    
                    message_dict["media"].append(media_info)
                    
                # Set overall media status for the message
                if all(m["status"] == "locked" for m in message_dict["media"]):
                    message_dict["media_status"] = "all_locked"
                elif any(m["status"] == "viewable" for m in message_dict["media"]):
                    message_dict["media_status"] = "some_viewable"
                else:
                    message_dict["media_status"] = "unknown"
            
            # Add preview information if available
            if hasattr(msg, 'previews') and msg.previews:
                message_dict["previews"] = []
                for preview in msg.previews:
                    preview_info = {
                        "type": getattr(preview, 'type', None),
                        "url": getattr(preview, 'url', None) if hasattr(preview, 'url') else None,
                    }
                    message_dict["previews"].append(preview_info)
            
            messages_data.append(message_dict)
        
        # Sort messages by date (newest first)
        messages_data.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"messages_with_media_{username}_{timestamp}.json"
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
            "statistics": {
                "ppv_messages": ppv_messages_count,
                "locked_media_items": locked_media_count,
                "viewable_media_items": viewable_media_count,
            },
            "messages": messages_data
        }
        
        # Write with pretty formatting
        with open(output_path, 'wb') as f:
            f.write(orjson.dumps(output_data, option=orjson.OPT_INDENT_2))
        
        logger.info(f"✓ Successfully saved {len(messages_data)} messages to {output_filename}")
        
        # Print enhanced summary statistics
        print(f"\n=== Enhanced Message Statistics for {user.username} ===")
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
        
        # Media statistics
        print(f"\n=== Media Statistics ===")
        print(f"Total media items found: {locked_media_count + viewable_media_count}")
        print(f"Viewable media items: {viewable_media_count}")
        print(f"Locked media items: {locked_media_count}")
        print(f"PPV messages: {ppv_messages_count}")
        
        # Count messages by media status
        all_locked = sum(1 for msg in messages_data if msg.get('media_status') == 'all_locked')
        some_viewable = sum(1 for msg in messages_data if msg.get('media_status') == 'some_viewable')
        
        print(f"\nMessages with all media locked: {all_locked}")
        print(f"Messages with some viewable media: {some_viewable}")
        
        if messages_data:
            # Find date range
            dates = [msg['created_at'] for msg in messages_data if msg['created_at']]
            if dates:
                oldest_date = min(dates)
                newest_date = max(dates)
                print(f"\nDate range: {oldest_date[:10]} to {newest_date[:10]}")
        
        print(f"\n✓ Data saved to: {output_path.absolute()}")
        
        # Provide guidance about locked media
        if locked_media_count > 0:
            print(f"\n⚠️  Note: {locked_media_count} media items are locked (PPV content).")
            print("These require purchase to view. The media details will be null/limited until purchased.")
        
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
        logger.exception("Full exception details:")
    
    finally:
        # Clean up
        await api.close_pools()
        logger.info("API connections closed")


if __name__ == "__main__":
    print("UltimaScraperAPI - Fetch All Messages with Enhanced Media Handling")
    print("=" * 60)
    print("This script will fetch ALL messages from a user with enhanced media information.")
    print("Note: PPV (pay-per-view) content will show as locked until purchased.")
    print()
    
    asyncio.run(fetch_all_messages_with_media())