#!/usr/bin/env python3
"""
Test if messages are being cached or if there's an issue with repeated calls
"""

import asyncio
import json
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
import time

async def test_repeated_calls():
    # Load auth
    auth_data = json.loads(Path("auth.json").read_text())
    
    # Create API and login
    api = OnlyFansAPI(UltimaScraperAPIConfig())
    authed = await api.login(auth_data["auth"])
    
    print(f"Authenticated as: {authed.username}")
    
    # Get a specific user
    user = await authed.get_user("heyitsmilliexx")
    if not user:
        print("User not found")
        return
    
    print(f"\nTesting repeated message fetches for: {user.username}")
    
    # Test multiple calls
    for i in range(5):
        print(f"\nAttempt {i+1}:")
        
        # Check if user has cache
        if hasattr(user, 'cache'):
            print(f"  Has cache attribute")
        
        # Get messages
        messages = await user.get_messages(limit=5)
        print(f"  Got {len(messages)} messages")
        
        if messages:
            print(f"  Latest message ID: {messages[0].id}")
            print(f"  Latest message text: {messages[0].text[:50] if messages[0].text else 'No text'}")
        
        # Wait a bit between calls
        if i < 4:
            print("  Waiting 3 seconds...")
            await asyncio.sleep(3)
    
    await api.close_pools()

if __name__ == "__main__":
    asyncio.run(test_repeated_calls())