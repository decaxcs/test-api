from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import json
from pathlib import Path
from functools import wraps
from datetime import datetime
import logging
import nest_asyncio

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
import ultima_scraper_api

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

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
            # Ensure the loop stays open during execution
            coro = asyncio.ensure_future(f(*args, **kwargs))
            result = loop.run_until_complete(coro)
            
            # Allow pending tasks to complete
            pending = asyncio.all_tasks(loop)
            if pending:
                # Give tasks a moment to finish
                loop.run_until_complete(asyncio.sleep(0.1))
                
                # Now cancel remaining tasks
                for task in pending:
                    if not task.done():
                        task.cancel()
                
                # Wait for cancellation
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            return result
        except Exception as e:
            logger.error(f"Async route error: {str(e)}")
            raise
        finally:
            # Clean shutdown
            try:
                # Cancel all remaining tasks
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.run_until_complete(asyncio.sleep(0))
                loop.close()
            except:
                pass
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

@app.route('/')
def home():
    return jsonify({
        "message": "UltimaScraperAPI Server",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "endpoints": [
            "/api/auth",
            "/api/docs", 
            "/api/me",
            "/api/user/<username>",
            "/api/user/<username>/posts",
            "/api/user/<username>/messages",
            "/api/user/<username>/stories",
            "/api/subscriptions"
        ]
    })

@app.route('/api/docs')
def api_documentation():
    """Return complete API documentation with all endpoints, parameters, and examples"""
    docs = {
        "title": "UltimaScraperAPI Documentation",
        "version": "1.0.0",
        "base_url": request.host_url.rstrip('/'),
        "authentication": {
            "description": "All endpoints except /api/auth require authentication via auth.json",
            "method": "First call /api/auth to authenticate, then use other endpoints"
        },
        "endpoints": [
            {
                "path": "/api/auth",
                "method": "POST",
                "description": "Authenticate with OnlyFans using cookies",
                "authentication_required": False,
                "request_body": {
                    "auth": {
                        "id": "numeric_user_id",
                        "cookie": "full_cookie_string", 
                        "x_bc": "browser_check_token",
                        "user_agent": "browser_user_agent"
                    }
                },
                "response": {
                    "success": True,
                    "message": "Authentication successful",
                    "user": {
                        "id": 123456,
                        "username": "username",
                        "name": "Display Name"
                    }
                },
                "example_curl": 'curl -X POST http://localhost:5000/api/auth -H "Content-Type: application/json" -d @auth.json'
            },
            {
                "path": "/api/me",
                "method": "GET",
                "description": "Get current authenticated user information",
                "authentication_required": True,
                "parameters": None,
                "response": {
                    "id": 123456,
                    "username": "myusername",
                    "name": "My Name",
                    "email": "email@example.com",
                    "avatar": "https://...",
                    "header": "https://...",
                    "bio": "Bio text",
                    "posts_count": 100,
                    "photos_count": 80,
                    "videos_count": 20,
                    "likes_count": 500,
                    "is_verified": True
                },
                "example_curl": "curl http://localhost:5000/api/me"
            },
            {
                "path": "/api/user/<username>",
                "method": "GET",
                "description": "Get profile information for a specific user",
                "authentication_required": True,
                "url_parameters": {
                    "username": "Username of the user to fetch"
                },
                "response": {
                    "id": 789012,
                    "username": "modelname",
                    "name": "Model Name",
                    "avatar": "https://...",
                    "header": "https://...",
                    "bio": "Bio text",
                    "posts_count": 500,
                    "photos_count": 400,
                    "videos_count": 100,
                    "joined": "2020-01-01",
                    "is_verified": True
                },
                "example_curl": "curl http://localhost:5000/api/user/modelname"
            },
            {
                "path": "/api/user/<username>/posts",
                "method": "GET",
                "description": "Get posts from a specific user",
                "authentication_required": True,
                "url_parameters": {
                    "username": "Username of the user"
                },
                "query_parameters": {
                    "limit": "Number of posts to fetch (default: 50, max: 100)",
                    "offset": "Pagination offset (default: 0)"
                },
                "response": {
                    "posts": [
                        {
                            "id": 123456789,
                            "text": "Post content",
                            "price": 0,
                            "created_at": "2025-01-01T00:00:00Z",
                            "likes_count": 100,
                            "comments_count": 50,
                            "is_pinned": False,
                            "media": [
                                {
                                    "id": 987654321,
                                    "type": "photo",
                                    "url": "https://...",
                                    "preview": "https://..."
                                }
                            ]
                        }
                    ],
                    "count": 50,
                    "limit": 50,
                    "offset": 0
                },
                "example_curl": "curl 'http://localhost:5000/api/user/modelname/posts?limit=10&offset=0'"
            },
            {
                "path": "/api/user/<username>/messages", 
                "method": "GET",
                "description": "Get messages exchanged with a specific user",
                "authentication_required": True,
                "url_parameters": {
                    "username": "Username of the user"
                },
                "query_parameters": {
                    "limit": "Number of messages to fetch (default: 50)",
                    "offset": "Pagination offset (default: 0)"
                },
                "response": {
                    "messages": [
                        {
                            "id": 111222333,
                            "text": "Message text",
                            "price": 0,
                            "created_at": "2025-01-01T00:00:00Z",
                            "is_read": True,
                            "is_from_user": False,
                            "media": []
                        }
                    ],
                    "count": 20,
                    "limit": 50,
                    "offset": 0
                },
                "example_curl": "curl 'http://localhost:5000/api/user/modelname/messages?limit=20'"
            },
            {
                "path": "/api/user/<username>/stories",
                "method": "GET", 
                "description": "Get stories from a specific user",
                "authentication_required": True,
                "url_parameters": {
                    "username": "Username of the user"
                },
                "response": {
                    "stories": [
                        {
                            "id": 444555666,
                            "created_at": "2025-01-01T00:00:00Z",
                            "expires_at": "2025-01-02T00:00:00Z",
                            "is_viewed": False,
                            "media": [
                                {
                                    "id": 777888999,
                                    "type": "photo",
                                    "url": "https://...",
                                    "preview": "https://..."
                                }
                            ]
                        }
                    ],
                    "count": 5
                },
                "example_curl": "curl http://localhost:5000/api/user/modelname/stories"
            },
            {
                "path": "/api/subscriptions",
                "method": "GET",
                "description": "Get list of your active subscriptions",
                "authentication_required": True,
                "query_parameters": {
                    "limit": "Number of subscriptions to fetch (default: 50)",
                    "offset": "Pagination offset (default: 0)"
                },
                "response": {
                    "subscriptions": [
                        {
                            "id": 123456,
                            "username": "modelname",
                            "name": "Model Name",
                            "avatar": "https://...",
                            "is_verified": True,
                            "subscription": {
                                "price": 999,
                                "status": "active",
                                "expires_at": "2025-02-01T00:00:00Z",
                                "renew": True
                            }
                        }
                    ],
                    "count": 10,
                    "limit": 50,
                    "offset": 0
                },
                "example_curl": "curl 'http://localhost:5000/api/subscriptions?limit=20'"
            }
        ],
        "error_responses": {
            "401": {
                "error": "Authentication required",
                "description": "You need to call /api/auth first"
            },
            "404": {
                "error": "User not found",
                "description": "The requested user does not exist"
            },
            "500": {
                "error": "Internal server error",
                "description": "Something went wrong on the server"
            }
        },
        "notes": [
            "All timestamps are in ISO 8601 format",
            "Prices are in cents (divide by 100 for dollars)",
            "Media URLs are temporary and IP-locked",
            "Rate limits apply - avoid making too many requests"
        ]
    }
    
    return jsonify(docs)

@app.route('/api/auth', methods=['POST'])
@async_route
async def authenticate():
    global api_instance, authed_instance
    
    try:
        data = request.get_json()
        if not data or 'auth' not in data:
            return jsonify({"error": "Missing auth data in request body"}), 400
        
        auth_data = data['auth']
        
        # Initialize API if not already done
        if not api_instance:
            config = UltimaScraperAPIConfig()
            api_instance = OnlyFansAPI(config)
            logger.info("Initialized OnlyFans API instance")
        
        # Authenticate
        logger.info("Attempting authentication...")
        authed_instance = await api_instance.login(auth_data)
        
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
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        user = await authed_instance.get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get messages with proper async handling
        messages = await user.get_messages(limit=limit, offset=offset)
        
        messages_data = []
        for msg in messages:
            # Get author info
            author = msg.get_author()
            is_from_user = author.id != authed_instance.user.id if authed_instance.user else False
            
            msg_dict = {
                "id": msg.id,
                "text": getattr(msg, 'text', ''),
                "price": getattr(msg, 'price', 0),
                "created_at": msg.created_at.isoformat() if hasattr(msg, 'created_at') else None,
                "is_read": getattr(msg, 'isOpened', True),
                "is_from_user": is_from_user,
                "from_user": {
                    "id": author.id,
                    "username": author.username,
                    "name": getattr(author, 'name', None)
                },
                "media": []
            }
            
            if hasattr(msg, 'media') and msg.media:
                for media_item in msg.media:
                    if isinstance(media_item, dict):
                        msg_dict["media"].append({
                            "id": media_item.get('id'),
                            "type": media_item.get('type', 'photo'),
                            "can_view": media_item.get('canView'),
                            "has_error": media_item.get('hasError', False)
                        })
                    else:
                        msg_dict["media"].append({
                            "id": getattr(media_item, 'id', None),
                            "type": getattr(media_item, 'type', 'photo'),
                            "url": getattr(media_item, 'url', None),
                            "preview": getattr(media_item, 'preview', None)
                        })
            
            messages_data.append(msg_dict)
        
        return jsonify({
            "messages": messages_data,
            "count": len(messages_data),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        logger.exception("Full traceback:")
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

# Cleanup on shutdown
import atexit

def cleanup():
    global api_instance
    if api_instance:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(api_instance.close_pools())
            loop.close()
            logger.info("API pools closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

atexit.register(cleanup)

if __name__ == '__main__':
    import socket
    
    # Configuration
    port = 5000
    host = '0.0.0.0'
    
    # Try to get the actual IP addresses
    hostname = socket.gethostname()
    try:
        # Get local network IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = socket.gethostbyname(hostname)
    
    # Try to get external IP (optional)
    external_ip = None
    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=2)
        external_ip = response.text
    except:
        pass
    
    print("=" * 60)
    print("Starting UltimaScraperAPI Flask Server...")
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  GET    /                      - Server info")
    print("  GET    /api/docs              - Complete API documentation")
    print("  POST   /api/auth              - Authenticate with OnlyFans")
    print("  GET    /api/me                - Get current user info")
    print("  GET    /api/user/<username>   - Get user profile")
    print("  GET    /api/user/<username>/posts    - Get user posts")
    print("  GET    /api/user/<username>/messages - Get messages with user")
    print("  GET    /api/user/<username>/stories  - Get user stories")
    print("  GET    /api/subscriptions     - Get your subscriptions")
    print("\n" + "=" * 60)
    print("Server Access URLs:")
    print(f"  Local:    http://localhost:{port}")
    print(f"  Network:  http://{local_ip}:{port}")
    if external_ip:
        print(f"  External: http://{external_ip}:{port}")
    print("=" * 60)
    print(f"\nListening on all interfaces ({host}:{port})")
    print("Press CTRL+C to quit")
    
    # First install nest_asyncio if not already installed
    try:
        import nest_asyncio
    except ImportError:
        print("\nIMPORTANT: Please install nest_asyncio first:")
        print("pip install nest-asyncio")
        exit(1)
    
    app.run(debug=True, host=host, port=port)