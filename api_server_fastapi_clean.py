from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import json
from pathlib import Path as FilePath
from datetime import datetime
import logging

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
    title="UltimaScraperAPI Server - Clean Version",
    description="A FastAPI server for UltimaScraperAPI with only working endpoints",
    version="2.0.0",
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

class MessageRequest(BaseModel):
    text: str
    media_ids: Optional[List[int]] = []

# Dependency to check authentication
async def require_auth():
    global authed_instance
    if not authed_instance or not authed_instance.is_authed():
        raise HTTPException(status_code=401, detail="Authentication required")
    return authed_instance

# Root endpoint
@app.get("/")
async def home():
    return {
        "message": "UltimaScraperAPI Server - Clean Version",
        "version": "2.0.0",
        "documentation": "/docs",
        "api_documentation": "/api/docs",
        "working_endpoints": [
            # System
            "/api/health",
            "/api/docs",
            # Authentication
            "/api/auth",
            # User Information
            "/api/me",
            "/api/user/{username}",
            # Content Retrieval
            "/api/user/{username}/posts",
            "/api/user/{username}/messages",
            "/api/user/{username}/stories",
            "/api/user/{username}/highlights",
            "/api/user/{username}/mass-messages",
            "/api/user/{username}/archived-stories",
            "/api/user/{username}/socials",
            # Subscriptions & Chats
            "/api/subscriptions",
            "/api/chats",
            "/api/mass-messages",
            # Messaging
            "/api/user/{username}/message",
            # Interactions
            "/api/post/{post_id}/like",
            "/api/user/{user_id}/block",
            # Financial
            "/api/transactions",
            "/api/paid-content",
            # Vault
            "/api/vault",
            # Promotions (Read-only)
            "/api/promotions"
        ]
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "UltimaScraperAPI FastAPI Server - Clean Version",
        "timestamp": datetime.now().isoformat()
    }

# API documentation endpoint
@app.get("/api/docs")
async def api_documentation():
    """Return API documentation for working endpoints only"""
    return {
        "title": "UltimaScraperAPI Documentation - Working Endpoints",
        "version": "2.0.0",
        "base_url": "http://localhost:5000",
        "authentication": {
            "description": "All endpoints except /api/auth require authentication via auth.json",
            "method": "First call /api/auth to authenticate, then use other endpoints"
        },
        "endpoints": {
            "authentication": {
                "/api/auth": {
                    "method": "POST",
                    "description": "Authenticate with OnlyFans",
                    "body": {"auth": {"id": "user_id", "cookie": "cookie_string", "x_bc": "browser_check", "user_agent": "user_agent_string"}},
                    "response": {"success": True, "message": "Authentication successful", "user": {}}
                }
            },
            "user_info": {
                "/api/me": {
                    "method": "GET",
                    "description": "Get current authenticated user information",
                    "auth_required": True,
                    "response": {"id": 123, "username": "user", "name": "Display Name"}
                },
                "/api/user/{username}": {
                    "method": "GET",
                    "description": "Get profile information for a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username"},
                    "response": {"id": 123, "username": "user", "name": "Display Name", "bio": "Bio text"}
                }
            },
            "content": {
                "/api/user/{username}/posts": {
                    "method": "GET",
                    "description": "Get posts from a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username", "limit": 50, "offset": 0},
                    "response": {"posts": [], "count": 25, "limit": 50, "offset": 0}
                },
                "/api/user/{username}/messages": {
                    "method": "GET",
                    "description": "Get message history with a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username", "limit": 50, "offset": 0},
                    "response": {"messages": [], "count": 25, "limit": 50, "offset": 0}
                }
            }
        }
    }

# Authentication endpoint
@app.post("/api/auth", response_model=AuthResponse)
async def authenticate(request: AuthRequest):
    global api_instance, authed_instance
    
    try:
        auth_data = request.auth
        if not auth_data:
            auth_path = FilePath("auth.json")
            if not auth_path.exists():
                raise HTTPException(status_code=400, detail="No auth data provided and auth.json not found")
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
            
            return AuthResponse(
                success=True,
                message="Authentication successful",
                user=user_info
            )
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# User Information Endpoints
@app.get("/api/me")
async def get_current_user(authed_instance=Depends(require_auth)):
    try:
        user = authed_instance.user
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
            "likes_count": getattr(user, 'likes_count', 0),
            "is_verified": getattr(user, 'is_verified', False)
        }
    
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}")
async def get_user(username: str = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(username)
        
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
            "is_verified": getattr(user, 'is_verified', False),
            "subscription_price": getattr(user, 'subscribe_price', 0),
            "promotions": getattr(user, 'promotions', [])
        }
    
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Content Endpoints
@app.get("/api/user/{username}/posts")
async def get_user_posts(
    username: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
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
    
    except Exception as e:
        logger.error(f"Get user posts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/messages")
async def get_user_messages(
    username: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        messages = await user.get_messages(limit=limit, offset=offset)
        
        messages_data = []
        for message in messages:
            message_dict = {
                "id": message.id,
                "text": message.text,
                "price": getattr(message, 'price', 0),
                "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                "is_read": getattr(message, 'is_read', False),
                "is_from_user": getattr(message, 'is_from_user', False),
                "media": []
            }
            
            if hasattr(message, 'media') and message.media:
                for media in message.media:
                    message_dict["media"].append({
                        "id": media.id,
                        "type": getattr(media, 'type', 'photo'),
                        "url": getattr(media, 'url', None),
                        "preview": getattr(media, 'preview', None)
                    })
            
            messages_data.append(message_dict)
        
        return {
            "messages": messages_data,
            "count": len(messages_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get user messages error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/stories")
async def get_user_stories(username: str = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stories = await user.get_stories()
        
        stories_data = []
        for story in stories:
            story_dict = {
                "id": story.id,
                "created_at": story.created_at.isoformat() if hasattr(story, 'created_at') else None,
                "expires_at": getattr(story, 'expires_at', None),
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
        
        return {"stories": stories_data}
    
    except Exception as e:
        logger.error(f"Get user stories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/highlights")
async def get_user_highlights(username: str = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        highlights = await user.get_highlights()
        
        highlights_data = []
        for highlight in highlights:
            highlights_data.append({
                "id": highlight.id,
                "title": getattr(highlight, 'title', ''),
                "cover": getattr(highlight, 'cover', None),
                "stories_count": getattr(highlight, 'stories_count', 0)
            })
        
        return {"highlights": highlights_data}
    
    except Exception as e:
        logger.error(f"Get user highlights error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/mass-messages")
async def get_user_mass_messages(
    username: str = Path(...),
    message_cutoff_id: int | None = Query(None),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        mass_messages = await user.get_mass_messages(message_cutoff_id=message_cutoff_id)
        
        mass_messages_data = []
        for message in mass_messages:
            mass_messages_data.append({
                "id": message.id,
                "text": getattr(message, 'text', ''),
                "price": getattr(message, 'price', 0),
                "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                "is_mass_message": True
            })
        
        return {"mass_messages": mass_messages_data}
    
    except Exception as e:
        logger.error(f"Get user mass messages error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/archived-stories")
async def get_archived_stories(
    username: str = Path(...),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        stories = await user.get_archived_stories(limit=limit, offset=offset)
        
        stories_data = []
        for story in stories:
            story_dict = {
                "id": story.id,
                "created_at": story.created_at.isoformat() if hasattr(story, 'created_at') else None,
                "expires_at": getattr(story, 'expires_at', None),
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
            "archived_stories": stories_data,
            "count": len(stories_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get archived stories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/socials")
async def get_user_socials(username: str = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        socials = await user.get_socials()
        
        return {"socials": socials}
    
    except Exception as e:
        logger.error(f"Get user socials error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Subscription and Social Endpoints
@app.get("/api/subscriptions")
async def get_subscriptions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        subscriptions = await authed_instance.get_subscriptions(limit=limit, offset=offset)
        
        subscriptions_data = []
        for subscription in subscriptions:
            subscriptions_data.append({
                "id": subscription.id,
                "username": subscription.username,
                "name": getattr(subscription, 'name', None),
                "avatar": getattr(subscription, 'avatar', None),
                "subscription_price": getattr(subscription, 'subscription_price', 0),
                "is_active": getattr(subscription, 'is_active', False)
            })
        
        return {
            "subscriptions": subscriptions_data,
            "count": len(subscriptions_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get subscriptions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chats")
async def get_chats(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        chats = await authed_instance.get_chats(limit=limit, offset=offset)
        
        chats_data = []
        for chat in chats:
            chats_data.append({
                "id": chat.id,
                "username": chat.username,
                "name": getattr(chat, 'name', None),
                "avatar": getattr(chat, 'avatar', None),
                "last_message": getattr(chat, 'last_message', None),
                "unread_count": getattr(chat, 'unread_count', 0)
            })
        
        return {
            "chats": chats_data,
            "count": len(chats_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get chats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mass-messages")
async def get_mass_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        mass_messages = await authed_instance.get_mass_message_stats(limit=limit, offset=offset)
        
        mass_messages_data = []
        for message in mass_messages:
            mass_messages_data.append({
                "id": message.id,
                "text": getattr(message, 'text', ''),
                "price": getattr(message, 'price', 0),
                "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                "stats": {
                    "sent_count": getattr(message, 'sent_count', 0),
                    "opened_count": getattr(message, 'opened_count', 0),
                    "revenue": getattr(message, 'revenue', 0)
                }
            })
        
        return {
            "mass_messages": mass_messages_data,
            "count": len(mass_messages_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get mass messages error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Messaging Endpoints
@app.post("/api/user/{username}/message")
async def send_message(
    username: str = Path(...),
    request: MessageRequest = Body(...),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        message = await user.send_message(
            text=request.text,
            media_ids=request.media_ids
        )
        
        if not message:
            raise HTTPException(status_code=400, detail="Failed to send message")
        
        return {
            "success": True,
            "message_id": message.id,
            "text": message.text,
            "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None
        }
    
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Interaction Endpoints
@app.post("/api/post/{post_id}/like")
async def like_post(post_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        # Find the post first to get its category
        # For now, assume it's a post (you might need to enhance this)
        result = await authed_instance.user.like("posts", post_id)
        return {"success": True, "liked": True}
    
    except Exception as e:
        logger.error(f"Like post error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/post/{post_id}/like")
async def unlike_post(post_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        result = await authed_instance.user.unlike("posts", post_id)
        return {"success": True, "liked": False}
    
    except Exception as e:
        logger.error(f"Unlike post error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{user_id}/block")
async def block_user(user_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await user.block()
        return {"success": True, "message": "User blocked successfully"}
    
    except Exception as e:
        logger.error(f"Block user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/{user_id}/block")
async def unblock_user(user_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        user = await authed_instance.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await user.unblock()
        return {"success": True, "message": "User unblocked successfully"}
    
    except Exception as e:
        logger.error(f"Unblock user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Financial Endpoints
@app.get("/api/transactions")
async def get_transactions(authed_instance=Depends(require_auth)):
    try:
        transactions = await authed_instance.get_transactions()
        
        return {
            "transactions": transactions,
            "count": len(transactions) if isinstance(transactions, list) else 0
        }
    
    except Exception as e:
        logger.error(f"Get transactions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/paid-content")
async def get_paid_content(
    performer_id: int | str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        paid_content = await authed_instance.get_paid_content(
            performer_id=performer_id,
            limit=limit,
            offset=offset
        )
        
        paid_content_data = []
        for content in paid_content:
            content_dict = {
                "id": content.id,
                "type": content.responseType,
                "text": getattr(content, 'text', ''),
                "price": getattr(content, 'price', 0),
                "author": {
                    "id": content.get_author().id,
                    "username": content.get_author().username
                },
                "created_at": content.created_at.isoformat() if hasattr(content, 'created_at') else None
            }
            paid_content_data.append(content_dict)
        
        return {
            "paid_content": paid_content_data,
            "count": len(paid_content_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get paid content error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Vault Endpoints
@app.get("/api/vault")
async def get_vault_media(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    authed_instance=Depends(require_auth)
):
    try:
        vault_media = await authed_instance.get_vault_media(limit=limit, offset=offset)
        
        vault_data = []
        for media in vault_media:
            vault_data.append({
                "id": media.get('id'),
                "type": media.get('type', 'photo'),
                "url": media.get('src'),
                "preview": media.get('preview'),
                "created_at": media.get('createdAt')
            })
        
        return {
            "vault_media": vault_data,
            "count": len(vault_data),
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Get vault media error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Promotions Endpoints (Read-only)
@app.get("/api/promotions")
async def get_promotions(authed_instance=Depends(require_auth)):
    try:
        # Get promotions from authenticated user's profile
        user = authed_instance.user
        promotions = user.promotions if hasattr(user, 'promotions') else []
        
        promotions_data = []
        for promotion in promotions:
            promotions_data.append({
                "id": promotion.get('id'),
                "discount": promotion.get('discount', 0),
                "price": promotion.get('price', 0),
                "duration": promotion.get('duration'),
                "is_active": promotion.get('isActive', False),
                "type": promotion.get('type')
            })
        
        return {"promotions": promotions_data}
    
    except Exception as e:
        logger.error(f"Get promotions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)