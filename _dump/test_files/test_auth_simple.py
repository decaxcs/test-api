import asyncio
import json
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

async def test_auth():
    # Load auth.json
    auth_data = json.loads(Path("auth.json").read_text())
    auth_details = auth_data["auth"]
    
    print(f"Testing with user ID: {auth_details['id']}")
    print(f"Cookie length: {len(auth_details['cookie'])} chars")
    
    # Create API and try to login
    api = OnlyFansAPI(UltimaScraperAPIConfig())
    
    # Try guest mode first
    print("\n1. Testing guest mode...")
    async with api.login_context(guest=True) as authed:
        if authed and authed.is_authed():
            print("✓ Guest mode works")
            user = await authed.get_user("onlyfans")
            if user:
                print(f"✓ Can fetch public user: {user.username}")
        else:
            print("✗ Guest mode failed")
    
    # Try auth mode
    print("\n2. Testing auth mode...")
    async with api.login_context(auth_json=auth_details) as authed:
        if authed and authed.is_authed():
            print("✓ Authentication successful!")
            # Try to get your own info
            if hasattr(authed, 'user') and authed.user:
                print(f"✓ Logged in as: {authed.user.username}")
        else:
            print("✗ Authentication failed")
            print("\nPossible reasons:")
            print("- Cookies expired (try getting fresh ones)")
            print("- Account requires 2FA")
            print("- IP address mismatch")

if __name__ == "__main__":
    asyncio.run(test_auth())