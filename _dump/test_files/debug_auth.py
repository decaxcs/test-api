# debug_auth.py
"""
Debug authentication issues
"""
import asyncio
import json
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Setup logging with DEBUG level
setup_logging(level=logging.DEBUG)
logger = get_logger(__name__)

# Also enable debug logging for the API modules
logging.getLogger("ultima_scraper_api").setLevel(logging.DEBUG)
logging.getLogger("ultima_scraper_api.apis.onlyfans").setLevel(logging.DEBUG)
logging.getLogger("ultima_scraper_api.apis.onlyfans.authenticator").setLevel(logging.DEBUG)


async def debug_authentication():
    logger.info("="*50)
    logger.info("Debugging Authentication Process")
    logger.info("="*50)
    
    # Load auth.json
    auth_path = Path("auth.json")
    if not auth_path.exists():
        logger.error(f"auth.json not found at: {auth_path.absolute()}")
        return
        
    logger.info(f"Loading auth.json from: {auth_path.absolute()}")
    auth_data = json.loads(auth_path.read_text())
    auth_details = auth_data["auth"]
    
    # Log auth details (safely)
    logger.info("Auth data structure:")
    logger.info(f"  - ID: {auth_details.get('id', 'MISSING')}")
    logger.info(f"  - Cookie length: {len(auth_details.get('cookie', ''))} chars")
    logger.info(f"  - Has x_bc: {'x_bc' in auth_details}")
    logger.info(f"  - Has user_agent: {'user_agent' in auth_details}")
    logger.info(f"  - Active: {auth_details.get('active', 'MISSING')}")
    
    # Check cookie format
    cookie = auth_details.get('cookie', '')
    if cookie:
        cookie_parts = cookie.split(';')
        logger.info(f"  - Cookie parts: {len(cookie_parts)}")
        # Check for required cookie components
        has_auth_id = any('auth_id=' in part for part in cookie_parts)
        has_sess = any('sess=' in part for part in cookie_parts)
        logger.info(f"  - Has auth_id: {has_auth_id}")
        logger.info(f"  - Has sess: {has_sess}")
    
    # Create API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    logger.info("\nAttempting authentication...")
    
    # Try to authenticate
    try:
        # First, let's check what the authenticator does
        from ultima_scraper_api.apis.onlyfans.authenticator import OnlyFansAuthenticator
        
        authenticator = OnlyFansAuthenticator(api)
        logger.info(f"Created authenticator: {type(authenticator).__name__}")
        
        # Try login
        result = await authenticator.login(auth_details)
        logger.info(f"Login result type: {type(result).__name__ if result else 'None'}")
        
        if result:
            logger.info(f"Authenticator is_authed: {authenticator.is_authed()}")
            if hasattr(authenticator, 'errors'):
                logger.error(f"Authenticator errors: {authenticator.errors}")
            if hasattr(authenticator, '__raw__'):
                raw_response = authenticator.__raw__
                if isinstance(raw_response, dict):
                    if 'error' in raw_response:
                        logger.error(f"API error response: {raw_response.get('error')}")
                    else:
                        logger.info(f"API response keys: {list(raw_response.keys())[:10]}...")
        else:
            logger.error("Login returned None")
            
    except Exception as e:
        logger.error(f"Exception during authentication: {type(e).__name__}: {str(e)}")
        logger.debug("Full exception:", exc_info=True)
    
    # Also try with the context manager
    logger.info("\nTrying with login_context...")
    async with api.login_context(auth_json=auth_details) as authed:
        if authed:
            logger.info(f"Auth context created: {type(authed).__name__}")
            logger.info(f"Is authed: {authed.is_authed()}")
            
            # Check if we can access basic info
            if authed.is_authed():
                try:
                    # Try to get the authenticated user's own info
                    me = authed.user
                    if me:
                        logger.info(f"✓ Logged in as: {getattr(me, 'username', 'Unknown')} (ID: {getattr(me, 'id', 'Unknown')})")
                    else:
                        logger.error("Could not get user info despite being authed")
                except Exception as e:
                    logger.error(f"Error getting user info: {e}")
        else:
            logger.error("Login context returned None")
    
    logger.info("\n" + "="*50)
    logger.info("Debug completed")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(debug_authentication())