# examples_detailed.py
"""
Example usage for UltimaScraperAPI with detailed logging
"""
import asyncio
import logging
from logging_config import setup_logging, get_logger
import json

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Setup logging
setup_logging(level=logging.DEBUG)
logger = get_logger(__name__)


async def onlyfans_example_detailed():
    logger.info("="*50)
    logger.info("Starting OnlyFans API example with detailed logging")
    logger.info("="*50)
    
    # Create configuration
    config = UltimaScraperAPIConfig()
    logger.debug(f"Created API configuration - Type: {type(config).__name__}")
    
    # Initialize API
    api = OnlyFansAPI(config)
    logger.debug(f"Initialized OnlyFans API - Type: {type(api).__name__}")
    
    # Login context
    logger.info("Attempting to establish login context...")
    async with api.login_context(guest=True) as authed:
        logger.info(f"Login context established - Auth type: {type(authed).__name__ if authed else 'None'}")
        
        if authed and authed.is_authed():
            logger.info("✓ Authentication successful")
            logger.debug(f"Auth session type: {type(authed.auth_session).__name__ if hasattr(authed, 'auth_session') else 'Unknown'}")
            
            # Fetch user
            username = "heyitsmilliexx"
            logger.info(f"\nFetching user: '{username}'")
            
            try:
                user = await authed.get_user(username)
                
                if user:
                    # Log user details
                    logger.info("✓ User fetched successfully")
                    user_info = {
                        'username': getattr(user, 'username', 'N/A'),
                        'id': getattr(user, 'id', 'N/A'),
                        'name': getattr(user, 'name', 'N/A'),
                        'is_verified': getattr(user, 'is_verified', 'N/A'),
                        'posts_count': getattr(user, 'posts_count', 'N/A'),
                        'photos_count': getattr(user, 'photos_count', 'N/A'),
                        'videos_count': getattr(user, 'videos_count', 'N/A'),
                    }
                    logger.info(f"User details: {json.dumps(user_info, indent=2)}")
                    
                    print(f"\nUser found: {user_info['username']} (ID: {user_info['id']})")
                    
                    # Try to fetch posts
                    logger.info(f"\nAttempting to fetch posts for user {username}")
                    try:
                        posts = await user.get_posts(limit=5)
                        logger.info(f"✓ Fetched {len(posts)} posts")
                        
                        for i, post in enumerate(posts[:3], 1):
                            logger.debug(f"Post {i} - ID: {getattr(post, 'id', 'N/A')}, Created: {getattr(post, 'created_at', 'N/A')}")
                    except Exception as e:
                        logger.error(f"✗ Failed to fetch posts: {type(e).__name__}: {str(e)}")
                    
                    # Try to fetch a specific post
                    post_id = 873482191
                    logger.info(f"\nAttempting to fetch specific post with ID: {post_id}")
                    
                    try:
                        post = await user.get_post(post_id)
                        logger.info(f"✓ Post fetched successfully")
                        logger.debug(f"Post details - ID: {post.id}, Created: {post.created_at}")
                        print(f"\nPost found: ID {post.id}, Created at {post.created_at}")
                    except Exception as e:
                        logger.error(f"✗ Failed to fetch post {post_id}: {type(e).__name__}: {str(e)}")
                        logger.debug("Exception details:", exc_info=True)
                    
                    # Try to check messages capability
                    logger.info(f"\nChecking message capabilities for user {username}")
                    if hasattr(user, 'get_messages'):
                        logger.info("✓ User object has get_messages method")
                        try:
                            # Just check if method exists, don't actually fetch
                            logger.info("Message fetching capability confirmed")
                        except Exception as e:
                            logger.error(f"Message method check failed: {str(e)}")
                    else:
                        logger.warning("✗ User object does not have get_messages method")
                        
                else:
                    logger.warning(f"✗ Failed to fetch user: {username}")
                    logger.debug("User fetch returned None or empty result")
                    
            except Exception as e:
                logger.error(f"✗ Exception during user fetch: {type(e).__name__}: {str(e)}")
                logger.debug("Full exception details:", exc_info=True)
                
        else:
            logger.error("✗ Authentication failed")
            logger.debug(f"Auth status - authed: {bool(authed)}, is_authed: {authed.is_authed() if authed else 'N/A'}")
    
    logger.info("\n" + "="*50)
    logger.info("Example completed")
    logger.info("="*50)


if __name__ == "__main__":
    logger.info("Script started")
    asyncio.run(onlyfans_example_detailed())
    logger.info("Script finished")