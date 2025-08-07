from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import json
from pathlib import Path
from datetime import datetime
import logging
import socket

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
import ultima_scraper_api

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
api_instance: Optional[OnlyFansAPI] = None
authed_instance = None

# Lifespan context manager for proper startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    global api_instance
    if api_instance:
        try:
            await api_instance.close_pools()
            logger.info("API pools closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="UltimaScraperAPI Server",
    description="A FastAPI server for UltimaScraperAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class AuthRequest(BaseModel):
    auth: Dict[str, Any]

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# Dependency to check authentication
async def require_auth():
    if not authed_instance or not authed_instance.is_authed():
        raise HTTPException(status_code=401, detail="Not authenticated. Please call /api/auth first")
    return authed_instance

@app.get("/")
async def home():
    return {
        "message": "UltimaScraperAPI Server (FastAPI)",
        "version": "1.0.0",
        "documentation": "/docs",
        "api_documentation": "/api/docs",
        "endpoints": [
            "/api/auth",
            "/api/docs",
            "/api/me",
            "/api/user/{username}",
            "/api/user/{username}/posts",
            "/api/user/{username}/messages",
            "/api/user/{username}/stories",
            "/api/subscriptions"
        ]
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "UltimaScraperAPI FastAPI Server",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/docs")
async def api_documentation():
    """Return complete API documentation"""
    return {
        "title": "UltimaScraperAPI Documentation",
        "version": "1.0.0",
        "base_url": "http://localhost:5000",
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
                }
            },
            {
                "path": "/api/me",
                "method": "GET",
                "description": "Get current authenticated user information",
                "authentication_required": True,
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
                }
            },
            {
                "path": "/api/user/{username}",
                "method": "GET",
                "description": "Get profile information for a specific user",
                "authentication_required": True,
                "url_parameters": {
                    "username": "Username of the user to fetch"
                }
            },
            {
                "path": "/api/user/{username}/posts",
                "method": "GET",
                "description": "Get posts from a specific user",
                "authentication_required": True,
                "query_parameters": {
                    "limit": "Number of posts to fetch (default: 50)",
                    "offset": "Pagination offset (default: 0)"
                }
            },
            {
                "path": "/api/user/{username}/messages",
                "method": "GET",
                "description": "Get messages exchanged with a specific user",
                "authentication_required": True,
                "query_parameters": {
                    "limit": "Number of messages to fetch (default: 50)",
                    "offset_id": "Message ID to start from for pagination (optional)"
                }
            },
            {
                "path": "/api/user/{username}/stories",
                "method": "GET",
                "description": "Get stories from a specific user",
                "authentication_required": True
            },
            {
                "path": "/api/subscriptions",
                "method": "GET",
                "description": "Get list of your active subscriptions",
                "authentication_required": True,
                "query_parameters": {
                    "limit": "Number of subscriptions to fetch (default: 50)",
                    "offset": "Pagination offset (default: 0)"
                }
            }
        ],
        "notes": [
            "All timestamps are in ISO 8601 format",
            "Prices are in cents (divide by 100 for dollars)",
            "Media URLs are temporary and IP-locked",
            "Rate limits apply - avoid making too many requests",
            "Use /docs for interactive API documentation"
        ]
    }

@app.post("/api/auth", response_model=AuthResponse)
async def authenticate(auth_request: AuthRequest):
    global api_instance, authed_instance
    
    try:
        auth_data = auth_request.auth
        
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
            
            return AuthResponse(
                success=True,
                message="Authentication successful",
                user=user_info
            )
        else:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": "Authentication failed",
                    "possible_reasons": [
                        "Cookies expired",
                        "Invalid credentials",
                        "Account requires 2FA",
                        "IP address mismatch"
                    ]
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/me")
async def get_me(auth = Depends(require_auth)):
    try:
        if hasattr(auth, 'user') and auth.user:
            user = auth.user
            return {
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
            }
        else:
            raise HTTPException(status_code=404, detail="User info not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get me error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}")
async def get_user(username: str, auth = Depends(require_auth)):
    try:
        user = await auth.get_user(username)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
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
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/posts")
async def get_user_posts(username: str, limit: int = 50, offset: int = 0, auth = Depends(require_auth)):
    try:
        user = await auth.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
        
        return {
            "posts": posts_data,
            "count": len(posts_data),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get posts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/messages")
async def get_user_messages(username: str, limit: int = 50, offset_id: Optional[int] = None, auth = Depends(require_auth)):
    try:
        user = await auth.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get messages
        messages = await user.get_messages(limit=limit, offset_id=offset_id)
        
        messages_data = []
        for msg in messages:
            # Get author info
            author = msg.get_author()
            is_from_user = author.id != auth.user.id if auth.user else False
            
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
        
        # Get the last message ID for pagination
        last_message_id = messages_data[-1]["id"] if messages_data else None
        
        return {
            "messages": messages_data,
            "count": len(messages_data),
            "limit": limit,
            "last_message_id": last_message_id,
            "pagination_hint": "Use last_message_id as offset_id for next page"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/stories")
async def get_user_stories(username: str, auth = Depends(require_auth)):
    try:
        user = await auth.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
        
        return {
            "stories": stories_data,
            "count": len(stories_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get stories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subscriptions")
async def get_subscriptions(limit: int = 50, offset: int = 0, auth = Depends(require_auth)):
    try:
        subscriptions = await auth.get_subscriptions(limit=limit, offset=offset)
        
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
        
        return {
            "subscriptions": subs_data,
            "count": len(subs_data),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscriptions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    port = 5000
    host = "0.0.0.0"
    
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
    print("Starting UltimaScraperAPI FastAPI Server...")
    print("=" * 60)
    print("\nAPI Endpoints:")
    print("  GET    /                      - Server info")
    print("  GET    /docs                  - Interactive API documentation")
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
    print(f"\nInteractive API Docs:")
    print(f"  Local:    http://localhost:{port}/docs")
    print(f"  Network:  http://{local_ip}:{port}/docs")
    print("=" * 60)
    print(f"\nListening on all interfaces ({host}:{port})")
    print("Press CTRL+C to quit")
    
    # Run the server
    uvicorn.run(app, host=host, port=port)