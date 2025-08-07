# example_with_auth.py
"""
Example showing how to use auth.json for authentication
"""
import asyncio
import json
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Setup logging
setup_logging(level=logging.DEBUG)
logger = get_logger(__name__)


async def login_with_auth_json():
    logger.info("="*50)
    logger.info("Starting OnlyFans API with auth.json")
    logger.info("="*50)
    
    # Check if auth.json exists
    auth_path = Path("auth.json")
    if not auth_path.exists():
        logger.error(f"❌ auth.json not found in current directory: {Path.cwd()}")
        logger.info("Please create an auth.json file with your authentication data")
        logger.info("Expected location: " + str(auth_path.absolute()))
        return
    
    # Load auth data
    try:
        logger.info(f"Loading auth.json from: {auth_path.absolute()}")
        auth_data = json.loads(auth_path.read_text())
        logger.info("✓ auth.json loaded successfully")
        
        # Check if auth key exists
        if "auth" not in auth_data:
            logger.error("❌ 'auth' key not found in auth.json")
            logger.info("Make sure your auth.json has the structure: {\"auth\": {...}}")
            return
            
        auth_details = auth_data["auth"]
        logger.debug(f"Auth data keys: {list(auth_details.keys())}")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in auth.json: {e}")
        return
    except Exception as e:
        logger.error(f"❌ Error loading auth.json: {e}")
        return
    
    # Create configuration
    config = UltimaScraperAPIConfig()
    logger.debug("Created API configuration")
    
    # Initialize API
    api = OnlyFansAPI(config)
    logger.debug("Initialized OnlyFans API")
    
    # Try to login with auth data
    logger.info("\nAttempting to login with auth.json credentials...")
    try:
        async with api.login_context(auth_json=auth_details) as authed:
            logger.info(f"Login context established - Type: {type(authed).__name__ if authed else 'None'}")
            
            if authed and authed.is_authed():
                logger.info("✓ Authentication successful!")
                logger.info("You are now logged in with real credentials")
                
                # Try to fetch a user
                username = "heyitsmilliexx"  # Change this to test different users
                logger.info(f"\nTesting by fetching user: '{username}'")
                
                user = await authed.get_user(username)
                if user:
                    logger.info(f"✓ Successfully fetched user: {user.username} (ID: {user.id})")
                    logger.info(f"  Posts: {getattr(user, 'posts_count', 'N/A')}")
                    logger.info(f"  Verified: {getattr(user, 'is_verified', 'N/A')}")
                else:
                    logger.warning(f"❌ Could not fetch user: {username}")
                    logger.info("This might mean the user doesn't exist or is blocked")
                    
            else:
                logger.error("❌ Authentication failed!")
                logger.info("Possible reasons:")
                logger.info("  - Invalid or expired cookies")
                logger.info("  - Incorrect auth.json format")
                logger.info("  - Account issues")
                
    except Exception as e:
        logger.error(f"❌ Login error: {type(e).__name__}: {str(e)}")
        logger.debug("Full error:", exc_info=True)
    
    logger.info("\n" + "="*50)
    logger.info("Example completed")
    logger.info("="*50)


async def show_auth_json_example():
    """Show example auth.json structure"""
    example = {
        "auth": {
            "id": 123456789,
            "username": "your_username",
            "cookie": "auth_id=xxx; sess=xxx; auth_hash=xxx; auth_uid_xxx=xxx; ...",
            "x_bc": "optional_token_here",
            "user_agent": "Mozilla/5.0 ...",
            "email": "optional@email.com",
            "password": "optional_password",
            "support_2fa": True
        }
    }
    
    logger.info("\nExample auth.json structure:")
    logger.info(json.dumps(example, indent=2))
    logger.info("\nNOTE: You need to get these values from your browser session")


if __name__ == "__main__":
    logger.info("Script started")
    
    # First show the example structure
    asyncio.run(show_auth_json_example())
    
    # Then try to login
    asyncio.run(login_with_auth_json())
    
    logger.info("Script finished")