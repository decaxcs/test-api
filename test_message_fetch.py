#!/usr/bin/env python3
"""
Quick test to check if we can fetch messages
"""

import asyncio
import json
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

async def test_messages():
    # Load auth
    auth_data = json.loads(Path("auth.json").read_text())
    
    # Create API and login
    api = OnlyFansAPI(UltimaScraperAPIConfig())
    authed = await api.login(auth_data["auth"])
    
    print(f"Authenticated as: {authed.username}")
    
    # Get chats
    chats = await authed.get_chats()
    print(f"\nFound {len(chats)} chats")
    
    # Test first few users
    for i, chat in enumerate(chats[:3]):
        user = chat.with_user if hasattr(chat, 'with_user') else chat.user
        print(f"\nUser {i+1}: {user.username} (ID: {user.id})")
        
        # Get messages
        messages = await user.get_messages(limit=5)
        print(f"  Got {len(messages)} messages")
        
        if messages:
            for j, msg in enumerate(messages[:3]):
                print(f"  Message {j+1}:")
                print(f"    ID: {msg.id}")
                print(f"    Text: {msg.text[:50] if msg.text else 'No text'}")
                print(f"    From user: {msg.is_from_user}")
                print(f"    Created: {msg.created_at}")
    
    await api.close_pools()

if __name__ == "__main__":
    asyncio.run(test_messages())