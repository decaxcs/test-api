# examples.py
"""
Example usage for UltimaScraperAPI with OnlyFansAPI.
"""
import asyncio
import logging
from logging_config import setup_logging, get_logger

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Setup logging
setup_logging(level=logging.DEBUG)
logger = get_logger(__name__)


async def onlyfans_example():
    logger.info("Starting OnlyFans API example")
    
    # Load auth.json
    import json
    from pathlib import Path
    
    auth_path = Path("auth.json")
    if auth_path.exists():
        logger.info("Loading auth.json...")
        auth_data = json.loads(auth_path.read_text())
        auth_details = auth_data["auth"]
        use_auth = True
    else:
        logger.warning("auth.json not found, using guest mode")
        auth_details = {}
        use_auth = False
    
    config = UltimaScraperAPIConfig()
    logger.debug("Created API configuration")
    
    api = OnlyFansAPI(config)
    logger.debug("Initialized OnlyFans API")
    
    # Create the appropriate login context
    async with api.login_context(auth_json=auth_details if use_auth else {}, guest=not use_auth) as authed:
        logger.info(f"Entered login context - Using {'auth.json' if use_auth else 'guest mode'}")
        
        if authed and authed.is_authed():
            logger.info("Authentication successful")
            
            username = "heyitsmilliexx"
            logger.info(f"Attempting to fetch user: {username}")
            
            user = await authed.get_user(username)
            
            if user:
                logger.info(f"User fetched successfully - Username: {getattr(user, 'username', None)}, ID: {getattr(user, 'id', None)}")
                print(
                    f"OnlyFans user: {getattr(user, 'username', None)} (ID: {getattr(user, 'id', None)})"
                )
                
                # post_id = 1813239887
                post_id = 1873462648
                logger.info(f"Attempting to fetch post with ID: {post_id}")
                
                try:
                    post = await user.get_post(post_id)
                    logger.info(f"Post fetched successfully - ID: {post.id}")
                    print(
                        f"Post ID: {post.id}, Title: {post.text}, Created At: {post.created_at}"
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch post {post_id}: {type(e).__name__}: {str(e)}")
                    logger.exception("Full exception details:")
            else:
                logger.warning(f"Failed to fetch user: {username}")
        else:
            logger.error("Authentication failed")


if __name__ == "__main__":
    asyncio.run(onlyfans_example())
