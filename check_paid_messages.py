#!/usr/bin/env python3
"""
Quick diagnostic to check for any paid messages in your chats
"""

import asyncio
import json
from pathlib import Path
import logging

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_paid_messages():
    # Load auth
    auth_data = json.loads(Path("auth.json").read_text())
    
    # Initialize API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    authed = await api.login(auth_data["auth"])
    
    if not authed:
        logger.error("Authentication failed!")
        return
    
    logger.info(f"Authenticated as: {authed.username}")
    
    # Get chats
    chats = await authed.get_chats(limit=10)
    
    print("\n" + "="*60)
    print("CHECKING FOR PAID MESSAGES")
    print("="*60)
    
    total_paid_found = 0
    
    for chat in chats:
        user = chat.user
        print(f"\n📍 Checking @{user.username}...")
        
        # Get messages
        messages = await user.get_messages(limit=100)
        
        paid_messages = []
        for msg in messages:
            price = getattr(msg, 'price', 0) or 0
            if price > 0:
                paid_messages.append({
                    'id': msg.id,
                    'price': price,
                    'price_dollars': price / 100,
                    'is_tip': getattr(msg, 'isTip', False),
                    'is_opened': getattr(msg, 'isOpened', False),
                    'is_free': getattr(msg, 'isFree', True),
                    'text': (getattr(msg, 'text', '')[:50] + "...") if getattr(msg, 'text', '') else "No text",
                    'created_at': msg.created_at.isoformat() if hasattr(msg, 'created_at') else None
                })
        
        if paid_messages:
            print(f"  ✅ Found {len(paid_messages)} paid messages:")
            for pm in paid_messages[:5]:  # Show first 5
                status = "✅ Opened" if pm['is_opened'] else "🔒 Locked"
                msg_type = "💝 Tip" if pm['is_tip'] else "💰 PPV"
                print(f"    {msg_type} ${pm['price_dollars']:.2f} - {status} - {pm['text']}")
            if len(paid_messages) > 5:
                print(f"    ... and {len(paid_messages) - 5} more")
            total_paid_found += len(paid_messages)
        else:
            print(f"  ❌ No paid messages found")
        
        # Also check paid content
        try:
            paid_content = await user.get_paid_contents()
            if paid_content:
                print(f"  📦 Also found {len(paid_content)} paid content items")
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"TOTAL PAID MESSAGES FOUND: {total_paid_found}")
    print(f"{'='*60}\n")
    
    await api.close_pools()


if __name__ == "__main__":
    asyncio.run(check_paid_messages())