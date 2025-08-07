from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import json
from pathlib import Path
from functools import wraps
from datetime import datetime
import logging
import time

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
import ultima_scraper_api

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_instance = None
authed_instance = None

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapped

def require_auth(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not authed_instance or not authed_instance.is_authed():
            return jsonify({"error": "Not authenticated. Please call /api/auth first"}), 401
        return await f(*args, **kwargs)
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "UltimaScraperAPI Wrapper",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/auth', methods=['POST'])
@async_route
async def authenticate():
    global api_instance, authed_instance
    
    try:
        auth_data = request.json
        if not auth_data:
            auth_path = Path("auth.json")
            if not auth_path.exists():
                return jsonify({"error": "No auth data provided and auth.json not found"}), 400
            auth_data = json.loads(auth_path.read_text())
        
        if "auth" in auth_data:
            auth_details = auth_data["auth"]
        else:
            auth_details = auth_data
        
        config = UltimaScraperAPIConfig()
        api_instance = OnlyFansAPI(config)
        
        authed_instance = await api_instance.login(auth_details)
        
        if authed_instance and authed_instance.is_authed():
            user_info = {}
            if hasattr(authed_instance, 'user') and authed_instance.user:
                user_info = {
                    "id": authed_instance.user.id,
                    "username": authed_instance.user.username,
                    "name": getattr(authed_instance.user, 'name', None)
                }
            
            return jsonify({
                "success": True,
                "message": "Authentication successful",
                "user": user_info
            })
        else:
            return jsonify({
                "success": False,
                "error": "Authentication failed",
                "possible_reasons": [
                    "Cookies expired",
                    "Invalid credentials",
                    "Account requires 2FA",
                    "IP address mismatch"
                ]
            }), 401
            
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/<username>', methods=['GET'])
@async_route
@require_auth
async def get_user(username):
    try:
        user = await authed_instance.get_user(username)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "name": getattr(user, 'name', None),
            "avatar": getattr(user, 'avatar', None),
            "header": getattr(user, 'header', None),
            "bio": getattr(user, 'raw_about', None),
            "posts_count": getattr(user, 'posts_count', 0),
            "photos_count": getattr(user, 'photos_count', 0),
            "videos_count": getattr(user, 'videos_count', 0),
            "joined": getattr(user, 'join_date', None),
            "is_verified": getattr(user, 'is_verified', False)
        })
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/<username>/posts', methods=['GET'])
@async_route
@require_auth
async def get_user_posts(username):
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        user = await authed_instance.get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        posts = await user.get_posts(limit=limit, offset=offset)
        
        posts_data = []
        for post in posts:
            post_dict = {
                "id": post.id,
                "text": post.text,
                "price": getattr(post, 'price', 0),
                "created_at": post.created_at.isoformat() if hasattr(post, 'created_at') else None,
                "likes_count": getattr(post, 'likes_count', 0),
                "comments_count": getattr(post, 'comments_count', 0),
                "is_pinned": getattr(post, 'is_pinned', False),
                "media": []
            }
            
            if hasattr(post, 'media') and post.media:
                for media in post.media:
                    post_dict["media"].append({
                        "id": media.id,
                        "type": getattr(media, 'type', 'photo'),
                        "url": getattr(media, 'url', None),
                        "preview": getattr(media, 'preview', None)
                    })
            
            posts_data.append(post_dict)
        
        return jsonify({
            "posts": posts_data,
            "count": len(posts_data),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Get posts error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/<username>/messages', methods=['GET'])
@async_route
@require_auth
async def get_user_messages(username):
    try:
        start_time = time.time()
        limit = request.args.get('limit', 20, type=int)  # Reduced default limit
        offset = request.args.get('offset', 0, type=int)
        
        logger.info(f"Fetching messages for {username} - limit: {limit}, offset: {offset}")
        
        # First check if user exists
        user = await authed_instance.get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"User found: {user.username}")
        
        # Set a timeout for message fetching
        try:
            messages = await asyncio.wait_for(
                user.get_messages(limit=limit, offset=offset),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Message fetch timed out")
            return jsonify({
                "error": "Request timed out. Try reducing the limit parameter.",
                "suggestion": "Try limit=5 or limit=10"
            }), 504
        
        logger.info(f"Fetched {len(messages) if messages else 0} messages")
        
        messages_data = []
        if messages:
            for msg in messages:
                try:
                    msg_dict = {
                        "id": msg.id,
                        "text": getattr(msg, 'text', ''),
                        "price": getattr(msg, 'price', 0),
                        "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None,
                        "is_read": getattr(msg, 'is_read', True),
                        "is_from_user": getattr(msg, 'is_from_user', False),
                        "media_count": len(msg.media) if hasattr(msg, 'media') and msg.media else 0
                    }
                    
                    # Only include basic media info to reduce response size
                    if hasattr(msg, 'media') and msg.media:
                        msg_dict["has_media"] = True
                    
                    messages_data.append(msg_dict)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
        
        elapsed_time = time.time() - start_time
        logger.info(f"Messages endpoint took {elapsed_time:.2f} seconds")
        
        return jsonify({
            "messages": messages_data,
            "count": len(messages_data),
            "limit": limit,
            "offset": offset,
            "processing_time": f"{elapsed_time:.2f}s"
        })
        
    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        return jsonify({
            "error": str(e),
            "suggestion": "Try with a smaller limit parameter (e.g., limit=5)"
        }), 500

@app.route('/api/user/<username>/messages/<message_id>', methods=['GET'])
@async_route
@require_auth
async def get_single_message(username, message_id):
    """Get details of a single message including media"""
    try:
        user = await authed_instance.get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get messages and find the specific one
        messages = await user.get_messages(limit=100)
        
        for msg in messages:
            if str(msg.id) == str(message_id):
                msg_dict = {
                    "id": msg.id,
                    "text": getattr(msg, 'text', ''),
                    "price": getattr(msg, 'price', 0),
                    "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None,
                    "is_read": getattr(msg, 'is_read', True),
                    "is_from_user": getattr(msg, 'is_from_user', False),
                    "media": []
                }
                
                if hasattr(msg, 'media') and msg.media:
                    for media in msg.media:
                        msg_dict["media"].append({
                            "id": media.id,
                            "type": getattr(media, 'type', 'photo'),
                            "url": getattr(media, 'url', None),
                            "preview": getattr(media, 'preview', None)
                        })
                
                return jsonify(msg_dict)
        
        return jsonify({"error": "Message not found"}), 404
        
    except Exception as e:
        logger.error(f"Get single message error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/<username>/stories', methods=['GET'])
@async_route
@require_auth
async def get_user_stories(username):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        stories = await user.get_stories()
        
        stories_data = []
        for story in stories:
            story_dict = {
                "id": story.id,
                "created_at": story.created_at.isoformat() if hasattr(story, 'created_at') else None,
                "expires_at": story.expires_at.isoformat() if hasattr(story, 'expires_at') else None,
                "is_viewed": getattr(story, 'is_viewed', False),
                "media": []
            }
            
            if hasattr(story, 'media') and story.media:
                for media in story.media:
                    story_dict["media"].append({
                        "id": media.id,
                        "type": getattr(media, 'type', 'photo'),
                        "url": getattr(media, 'url', None),
                        "preview": getattr(media, 'preview', None)
                    })
            
            stories_data.append(story_dict)
        
        return jsonify({
            "stories": stories_data,
            "count": len(stories_data)
        })
        
    except Exception as e:
        logger.error(f"Get stories error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/subscriptions', methods=['GET'])
@async_route
@require_auth
async def get_subscriptions():
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        subscriptions = await authed_instance.get_subscriptions(limit=limit, offset=offset)
        
        subs_data = []
        for sub in subscriptions:
            user = sub.user if hasattr(sub, 'user') else sub
            sub_dict = {
                "id": user.id,
                "username": user.username,
                "name": getattr(user, 'name', None),
                "avatar": getattr(user, 'avatar', None),
                "is_verified": getattr(user, 'is_verified', False),
                "subscription": {
                    "price": getattr(sub, 'price', 0),
                    "status": getattr(sub, 'status', 'active'),
                    "expires_at": sub.expires_at.isoformat() if hasattr(sub, 'expires_at') else None,
                    "renew": getattr(sub, 'renew', True)
                }
            }
            subs_data.append(sub_dict)
        
        return jsonify({
            "subscriptions": subs_data,
            "count": len(subs_data),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Get subscriptions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/me', methods=['GET'])
@async_route
@require_auth
async def get_me():
    try:
        if hasattr(authed_instance, 'user') and authed_instance.user:
            user = authed_instance.user
            return jsonify({
                "id": user.id,
                "username": user.username,
                "name": getattr(user, 'name', None),
                "email": getattr(user, 'email', None),
                "avatar": getattr(user, 'avatar', None),
                "header": getattr(user, 'header', None),
                "bio": getattr(user, 'raw_about', None),
                "posts_count": getattr(user, 'posts_count', 0),
                "photos_count": getattr(user, 'photos_count', 0),
                "videos_count": getattr(user, 'videos_count', 0),
                "likes_count": getattr(user, 'likes_count', 0),
                "is_verified": getattr(user, 'is_verified', False)
            })
        else:
            return jsonify({"error": "User info not available"}), 404
            
    except Exception as e:
        logger.error(f"Get me error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("Starting UltimaScraperAPI Flask Server...")
    print("API Documentation:")
    print("  POST   /api/auth              - Authenticate with OnlyFans")
    print("  GET    /api/me                - Get current user info")
    print("  GET    /api/user/<username>   - Get user profile")
    print("  GET    /api/user/<username>/posts    - Get user posts")
    print("  GET    /api/user/<username>/messages - Get messages with user")
    print("  GET    /api/user/<username>/messages/<id> - Get single message details")
    print("  GET    /api/user/<username>/stories  - Get user stories")
    print("  GET    /api/subscriptions     - Get your subscriptions")
    print("\nServer running on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)