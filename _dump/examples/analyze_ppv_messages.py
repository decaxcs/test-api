#!/usr/bin/env python3
"""
Analyze PPV Messages and Media
This script analyzes pay-per-view messages and provides options to view/purchase content.
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


async def analyze_ppv_messages():
    """
    Analyzes PPV messages and provides detailed media information.
    """
    logger.info("Starting PPV message analysis")
    
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
        
        # Get username to analyze
        username = input("Enter username to analyze PPV messages from: ").strip()
        if not username:
            logger.error("Username is required!")
            return
        
        logger.info(f"Fetching user: {username}")
        user = await authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        
        # Fetch recent messages to analyze
        logger.info("Fetching recent messages...")
        messages = await user.get_messages(limit=50)
        
        if not messages:
            logger.info("No messages found")
            return
        
        # Analyze PPV messages
        ppv_messages = []
        free_with_media = []
        
        for msg in messages:
            msg_info = {
                "id": msg.id,
                "text": msg.text[:100] + "..." if msg.text and len(msg.text) > 100 else msg.text,
                "price": msg.price,
                "price_dollars": msg.price / 100 if msg.price else 0,
                "media_count": msg.media_count or 0,
                "can_purchase": msg.canPurchase,
                "is_opened": msg.isOpened,
                "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') and msg.created_at else None,
                "media_details": []
            }
            
            # Analyze media
            if hasattr(msg, 'media') and msg.media:
                for media_item in msg.media:
                    if isinstance(media_item, dict):
                        media_detail = {
                            "id": media_item.get('id'),
                            "type": media_item.get('type'),
                            "can_view": media_item.get('canView'),
                            "is_locked": media_item.get('isLocked', False),
                            "has_preview": bool(media_item.get('preview')),
                            "has_thumb": bool(media_item.get('thumb')),
                        }
                        
                        # Try to get dimensions for images/videos
                        if media_item.get('type') in ['photo', 'video']:
                            media_detail["width"] = media_item.get('width')
                            media_detail["height"] = media_item.get('height')
                            if media_item.get('type') == 'video':
                                media_detail["duration"] = media_item.get('duration')
                        
                        msg_info["media_details"].append(media_detail)
            
            # Categorize messages
            if msg.price and msg.price > 0:
                ppv_messages.append(msg_info)
            elif msg.media_count > 0:
                free_with_media.append(msg_info)
        
        # Display analysis results
        print(f"\n=== PPV Message Analysis for {user.username} ===")
        print(f"Total messages analyzed: {len(messages)}")
        print(f"PPV messages found: {len(ppv_messages)}")
        print(f"Free messages with media: {len(free_with_media)}")
        
        if ppv_messages:
            print(f"\n=== PPV Messages (Pay-Per-View) ===")
            total_ppv_cost = 0
            
            for i, msg in enumerate(ppv_messages, 1):
                print(f"\n{i}. Message ID: {msg['id']}")
                print(f"   Price: ${msg['price_dollars']:.2f}")
                print(f"   Media count: {msg['media_count']}")
                print(f"   Can purchase: {msg['can_purchase']}")
                print(f"   Already opened: {msg['is_opened']}")
                print(f"   Created: {msg['created_at'][:10] if msg['created_at'] else 'Unknown'}")
                
                if msg['text']:
                    print(f"   Preview text: {msg['text']}")
                
                if msg['media_details']:
                    print("   Media breakdown:")
                    for j, media in enumerate(msg['media_details'], 1):
                        print(f"     {j}. Type: {media['type'] or 'Unknown'}")
                        print(f"        Can view: {media['can_view']}")
                        print(f"        Locked: {media['is_locked']}")
                        if media.get('width') and media.get('height'):
                            print(f"        Resolution: {media['width']}x{media['height']}")
                        if media.get('duration'):
                            print(f"        Duration: {media['duration']}s")
                
                total_ppv_cost += msg['price_dollars']
            
            print(f"\n=== PPV Summary ===")
            print(f"Total PPV messages: {len(ppv_messages)}")
            print(f"Total cost if all purchased: ${total_ppv_cost:.2f}")
            
            # Count media types
            photo_count = sum(1 for msg in ppv_messages for media in msg['media_details'] if media['type'] == 'photo')
            video_count = sum(1 for msg in ppv_messages for media in msg['media_details'] if media['type'] == 'video')
            
            print(f"Total photos in PPV: {photo_count}")
            print(f"Total videos in PPV: {video_count}")
        
        # Save detailed analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"ppv_analysis_{username}_{timestamp}.json"
        output_path = Path(output_filename)
        
        output_data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
            },
            "analysis_date": datetime.now().isoformat(),
            "summary": {
                "total_messages_analyzed": len(messages),
                "ppv_message_count": len(ppv_messages),
                "free_media_message_count": len(free_with_media),
                "total_ppv_cost": sum(msg['price_dollars'] for msg in ppv_messages),
            },
            "ppv_messages": ppv_messages,
            "free_media_messages": free_with_media,
        }
        
        with open(output_path, 'wb') as f:
            f.write(orjson.dumps(output_data, option=orjson.OPT_INDENT_2))
        
        print(f"\n✓ Detailed analysis saved to: {output_path.absolute()}")
        
        # Provide guidance
        print("\n=== Understanding Media Status ===")
        print("• can_view: null - Media details not loaded (common for unpurchased PPV)")
        print("• can_view: false - Media is locked and requires purchase")
        print("• can_view: true - Media is accessible and URLs can be retrieved")
        print("• is_locked: true - Content is behind a paywall")
        
        print("\n⚠️  WARNING: The buy_message() method will spend real money!")
        print("To purchase a PPV message programmatically:")
        print("1. Use message.buy_message() method")
        print("2. Then use message.refresh() to get updated media URLs")
        print("3. Media URLs will then be available via message.url_picker()")
        
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
        logger.exception("Full exception details:")
    
    finally:
        # Clean up
        await api.close_pools()
        logger.info("API connections closed")


if __name__ == "__main__":
    print("UltimaScraperAPI - PPV Message Analyzer")
    print("=" * 50)
    print("This script analyzes pay-per-view messages and media status.")
    print("It helps understand why media information might be null.")
    print()
    
    asyncio.run(analyze_ppv_messages())