#!/usr/bin/env python3
"""
Test script to diagnose message fetching consistency issues
"""

import asyncio
import json
from pathlib import Path
import logging
from datetime import datetime
import time

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_message_consistency(username: str, authed_api, iterations: int = 5):
    """Test message fetching consistency for a user"""
    
    results = {
        "username": username,
        "iterations": [],
        "summary": {}
    }
    
    user = await authed_api.get_user(username)
    if not user:
        logger.error(f"User {username} not found")
        return results
    
    logger.info(f"Testing message consistency for {username} (ID: {user.id})")
    
    message_counts = []
    
    for i in range(iterations):
        iteration_data = {
            "iteration": i + 1,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Basic get_messages
        try:
            start_time = time.time()
            messages = await user.get_messages(limit=20)
            elapsed = time.time() - start_time
            
            iteration_data["tests"]["basic"] = {
                "success": True,
                "message_count": len(messages),
                "elapsed_time": f"{elapsed:.2f}s",
                "first_message": messages[0].text[:30] if messages else None,
                "message_ids": [msg.id for msg in messages[:5]] if messages else []
            }
            message_counts.append(len(messages))
            
        except Exception as e:
            iteration_data["tests"]["basic"] = {
                "success": False,
                "error": str(e)
            }
            message_counts.append(0)
        
        # Test 2: Check cache status
        try:
            cache_status = {
                "messages_cached": hasattr(user.cache, 'messages') and user.cache.messages.is_released(),
                "cache_active": hasattr(user.cache, 'messages') and user.cache.messages.is_active() if hasattr(user.cache, 'messages') else None
            }
            iteration_data["tests"]["cache_status"] = cache_status
        except Exception as e:
            iteration_data["tests"]["cache_status"] = {"error": str(e)}
        
        # Test 3: Try with different parameters
        try:
            messages_no_limit = await user.get_messages()
            iteration_data["tests"]["no_limit"] = {
                "success": True,
                "message_count": len(messages_no_limit)
            }
        except Exception as e:
            iteration_data["tests"]["no_limit"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 4: Check session status
        try:
            session_info = {
                "is_authed": user.get_authed().is_authed() if hasattr(user, 'get_authed') else None,
                "user_id": user.id,
                "username": user.username
            }
            iteration_data["tests"]["session"] = session_info
        except Exception as e:
            iteration_data["tests"]["session"] = {"error": str(e)}
        
        results["iterations"].append(iteration_data)
        
        # Wait between iterations to avoid rate limiting
        if i < iterations - 1:
            logger.info(f"Waiting 2 seconds before next iteration...")
            await asyncio.sleep(2)
    
    # Calculate summary statistics
    results["summary"] = {
        "total_iterations": iterations,
        "message_counts": message_counts,
        "consistent": len(set(message_counts)) == 1,
        "min_messages": min(message_counts) if message_counts else 0,
        "max_messages": max(message_counts) if message_counts else 0,
        "avg_messages": sum(message_counts) / len(message_counts) if message_counts else 0,
        "zero_count_iterations": message_counts.count(0)
    }
    
    return results


async def test_multiple_users(usernames: list, authed_api):
    """Test multiple users to see if it's user-specific"""
    all_results = {}
    
    for username in usernames:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing user: {username}")
        logger.info(f"{'='*50}")
        
        results = await test_message_consistency(username, authed_api, iterations=3)
        all_results[username] = results
        
        # Print summary
        summary = results["summary"]
        logger.info(f"\nSummary for {username}:")
        logger.info(f"  Consistent: {summary['consistent']}")
        logger.info(f"  Message counts: {summary['message_counts']}")
        logger.info(f"  Zero results: {summary['zero_count_iterations']} out of {summary['total_iterations']}")
        
        await asyncio.sleep(3)  # Wait between users
    
    return all_results


async def check_api_endpoints(authed_api):
    """Check various API endpoints to diagnose issues"""
    logger.info("\nChecking API endpoints...")
    
    checks = {}
    
    # Check 1: Can we get chats?
    try:
        chats = await authed_api.get_chats(limit=10)
        checks["chats"] = {
            "success": True,
            "count": len(chats),
            "sample_users": [chat.user.username for chat in chats[:3] if hasattr(chat, 'user') and chat.user]
        }
    except Exception as e:
        checks["chats"] = {"success": False, "error": str(e)}
    
    # Check 2: Can we get our own user info?
    try:
        me = authed_api.user
        checks["self_info"] = {
            "success": True,
            "username": me.username if me else None,
            "id": me.id if me else None
        }
    except Exception as e:
        checks["self_info"] = {"success": False, "error": str(e)}
    
    # Check 3: Session manager status
    try:
        session_manager = authed_api.session_manager
        checks["session"] = {
            "success": True,
            "has_session": session_manager is not None,
            "pool_limit": getattr(session_manager, 'pool_limit', None),
            "proxies": bool(getattr(session_manager, 'proxies', None))
        }
    except Exception as e:
        checks["session"] = {"success": False, "error": str(e)}
    
    return checks


async def main():
    """Main test function"""
    try:
        # Load authentication
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json not found!")
            return
        
        auth_data = json.loads(auth_path.read_text())
        
        # Initialize API
        config = UltimaScraperAPIConfig()
        api = OnlyFansAPI(config)
        
        # Authenticate
        logger.info("Authenticating...")
        authed = await api.login(auth_data["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
        
        logger.info(f"Authenticated as: {authed.username}")
        
        # Check API endpoints first
        api_checks = await check_api_endpoints(authed)
        logger.info(f"\nAPI Endpoint Checks:")
        for check, result in api_checks.items():
            logger.info(f"  {check}: {result}")
        
        # Test specific users
        test_users = ["ariawolftv", "heyitsmilliexx"]
        
        logger.info(f"\nTesting message consistency for users: {test_users}")
        results = await test_multiple_users(test_users, authed)
        
        # Save results
        output_file = f"message_consistency_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        
        # Print recommendations
        logger.info("\n" + "="*60)
        logger.info("RECOMMENDATIONS:")
        logger.info("="*60)
        
        for username, user_results in results.items():
            summary = user_results["summary"]
            if not summary["consistent"]:
                logger.info(f"\n❌ {username} has inconsistent results!")
                if summary["zero_count_iterations"] > 0:
                    logger.info(f"   - Got 0 messages in {summary['zero_count_iterations']} iterations")
                    logger.info("   - This suggests rate limiting or session issues")
                    logger.info("   - Try: Adding delays between requests")
                    logger.info("   - Try: Refreshing auth cookies")
            else:
                logger.info(f"\n✅ {username} has consistent results ({summary['avg_messages']} messages)")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())