from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import asyncio
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

class MassMessageRequest(BaseModel):
    text: str
    media_ids: Optional[List[int]] = []
    price: Optional[int] = 0  # Price in cents (0 for free message)
    locked_text: Optional[bool] = False  # Whether the text is locked until paid

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
            "/api/messages/all",
            "/api/messages/all/detailed",
            "/api/mass-messages",
            # Messaging
            "/api/user/{username}/message",
            "/api/messages/mass-send",
            "/api/messages/mass-send/filtered",
            # Interactions
            "/api/post/{post_id}",
            "/api/post/{post_id}/like",
            "/api/user/{user_id}/block",
            # Financial
            "/api/transactions",
            "/api/paid-content",
            # Vault
            "/api/vault",
            # Promotions (Read-only)
            "/api/promotions",
            # Debug & Testing
            "/api/debug/user/{username}/messages",
            "/api/test/user/{username}/message-access"
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
    """Return comprehensive API documentation"""
    return {
        "title": "UltimaScraperAPI Documentation - Complete Reference",
        "version": "2.0.0",
        "base_url": "http://localhost:5000",
        "authentication": {
            "description": "All endpoints except /api/auth require authentication via auth.json",
            "method": "First call /api/auth to authenticate, then use other endpoints",
            "auth_format": {
                "auth": {
                    "id": "numeric_user_id",
                    "cookie": "full_cookie_string",
                    "x_bc": "browser_check_token",
                    "user_agent": "browser_user_agent_string"
                }
            }
        },
        "endpoints": {
            "authentication": {
                "/api/auth": {
                    "method": "POST",
                    "description": "Authenticate with OnlyFans using cookies",
                    "body": {"auth": {"id": "user_id", "cookie": "cookie_string", "x_bc": "browser_check", "user_agent": "user_agent_string"}},
                    "response": {"success": True, "message": "Authentication successful", "user": {"id": 123, "username": "username", "name": "Display Name"}}
                }
            },
            "user_info": {
                "/api/me": {
                    "method": "GET",
                    "description": "Get current authenticated user information",
                    "auth_required": True,
                    "response": {
                        "id": 123456,
                        "username": "myusername",
                        "name": "My Display Name",
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
                "/api/user/{username}": {
                    "method": "GET",
                    "description": "Get profile information for a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username"},
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
                        "is_verified": True,
                        "subscription_price": 999,
                        "promotions": []
                    }
                }
            },
            "content": {
                "/api/user/{username}/posts": {
                    "method": "GET",
                    "description": "Get posts from a specific user",
                    "auth_required": True,
                    "parameters": {
                        "username": "OnlyFans username",
                        "limit": "Number of posts (default: 50, max: 100)",
                        "label": "Filter by label: archived, private_archived",
                        "after_date": "Unix timestamp to get posts after"
                    },
                    "response": {
                        "posts": [{
                            "id": 123456789,
                            "text": "Post content",
                            "raw_text": "Post content without HTML",
                            "price": 0,
                            "created_at": "2025-01-01T00:00:00Z",
                            "likes_count": 100,
                            "comments_count": 50,
                            "is_pinned": False,
                            "is_archived": False,
                            "media": []
                        }],
                        "count": 50,
                        "limit": 50,
                        "label": "",
                        "after_date": None
                    }
                },
                "/api/user/{username}/messages": {
                    "method": "GET",
                    "description": "Get message history with a specific user",
                    "auth_required": True,
                    "parameters": {
                        "username": "OnlyFans username",
                        "limit": "Number of messages (default: 20, max: 100)",
                        "offset_id": "Message ID to start from (pagination)",
                        "cutoff_id": "Message ID to stop at"
                    },
                    "response": {
                        "user": {"id": 123, "username": "username", "name": "Name"},
                        "fetch_date": "2025-01-01T00:00:00Z",
                        "total_messages": 50,
                        "statistics": {
                            "ppv_messages": 10,
                            "locked_media_items": 5,
                            "viewable_media_items": 20
                        },
                        "messages": [{
                            "id": 111222333,
                            "text": "Message text",
                            "price": 0,
                            "price_dollars": 0,
                            "is_free": True,
                            "is_tip": False,
                            "is_opened": True,
                            "is_new": False,
                            "created_at": "2025-01-01T00:00:00Z",
                            "media": []
                        }]
                    }
                },
                "/api/user/{username}/stories": {
                    "method": "GET",
                    "description": "Get stories from a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username"},
                    "response": {
                        "stories": [{
                            "id": 444555666,
                            "created_at": "2025-01-01T00:00:00Z",
                            "expires_at": "2025-01-02T00:00:00Z",
                            "is_viewed": False,
                            "media": []
                        }]
                    }
                },
                "/api/user/{username}/highlights": {
                    "method": "GET",
                    "description": "Get highlights from a specific user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username"},
                    "response": {
                        "highlights": [{
                            "id": 123456,
                            "title": "Highlight Title",
                            "cover": "https://...",
                            "stories_count": 10
                        }]
                    }
                },
                "/api/user/{username}/mass-messages": {
                    "method": "GET",
                    "description": "Get mass messages FROM a specific user (promotional messages)",
                    "auth_required": True,
                    "parameters": {
                        "username": "OnlyFans username",
                        "message_cutoff_id": "Optional message ID cutoff",
                        "limit": "Number of messages to check (default: 100)"
                    },
                    "response": {
                        "mass_messages": [{
                            "id": 123456,
                            "text": "Promotional message",
                            "price": 0,
                            "created_at": "2025-01-01T00:00:00Z",
                            "is_mass_message": True,
                            "queue_info": {
                                "queue_id": 27138196267,
                                "is_from_queue": True,
                                "can_unsend_queue": False
                            }
                        }],
                        "count": 10,
                        "total_messages_checked": 100
                    }
                },
                "/api/user/{username}/archived-stories": {
                    "method": "GET",
                    "description": "Get archived stories from a specific user",
                    "auth_required": True,
                    "parameters": {
                        "username": "OnlyFans username",
                        "limit": "Number of stories (default: 100)",
                        "offset": "Pagination offset"
                    },
                    "response": {"archived_stories": [], "count": 0, "limit": 100, "offset": 0}
                },
                "/api/user/{username}/socials": {
                    "method": "GET",
                    "description": "Get social media links for a user",
                    "auth_required": True,
                    "parameters": {"username": "OnlyFans username"},
                    "response": {"socials": []}
                }
            },
            "subscriptions_chats": {
                "/api/subscriptions": {
                    "method": "GET",
                    "description": "Get list of your active subscriptions",
                    "auth_required": True,
                    "parameters": {
                        "limit": "Number of subscriptions (default: 50)",
                        "sub_type": "Type: all, active, expired, attention",
                        "filter_by": "Additional filter value"
                    },
                    "response": {
                        "subscriptions": [{
                            "id": 123456,
                            "username": "modelname",
                            "name": "Model Name",
                            "avatar": "https://...",
                            "subscription_price": 999,
                            "is_active": True,
                            "expire_date": "2025-02-01T00:00:00Z"
                        }],
                        "count": 10
                    }
                },
                "/api/chats": {
                    "method": "GET",
                    "description": "Get list of your message chats",
                    "auth_required": True,
                    "parameters": {
                        "limit": "Number of chats (default: 50)",
                        "offset": "Pagination offset"
                    },
                    "response": {
                        "chats": [{
                            "id": 123456,
                            "username": "username",
                            "name": "Display Name",
                            "avatar": "https://...",
                            "last_message": {"id": 111, "text": "Last message", "created_at": "2025-01-01T00:00:00Z"}
                        }],
                        "count": 50
                    }
                },
                "/api/messages/all": {
                    "method": "GET",
                    "description": "Get all messages from all chats",
                    "auth_required": True,
                    "parameters": {
                        "limit_per_chat": "Max messages per chat (default: 50)",
                        "include_purchases": "Include PPV purchases (default: true)"
                    },
                    "response": {
                        "total_messages": 500,
                        "total_chats": 10,
                        "chat_summaries": [],
                        "messages": []
                    }
                },
                "/api/messages/all/detailed": {
                    "method": "GET",
                    "description": "Get all messages with detailed statistics and filtering",
                    "auth_required": True,
                    "parameters": {
                        "limit_per_chat": "Max messages per chat (default: 100)",
                        "include_purchases": "Include PPV purchases",
                        "include_tips": "Include tip messages",
                        "only_with_media": "Only messages with media"
                    },
                    "response": {
                        "statistics": {
                            "total_messages": 1000,
                            "total_chats": 20,
                            "ppv_messages": 50,
                            "tip_messages": 30,
                            "total_spent": 50000
                        },
                        "chats": [],
                        "messages": []
                    }
                },
                "/api/mass-messages": {
                    "method": "GET",
                    "description": "Get your sent mass message campaigns",
                    "auth_required": True,
                    "parameters": {
                        "limit": "Number of campaigns (default: 50)",
                        "offset": "Pagination offset"
                    },
                    "response": {"mass_messages": [], "count": 0}
                }
            },
            "messaging": {
                "/api/user/{username}/message": {
                    "method": "POST",
                    "description": "Send a message to a specific user",
                    "auth_required": True,
                    "parameters": {"username": "Recipient username"},
                    "body": {
                        "text": "Message text",
                        "media_ids": [123, 456]
                    },
                    "response": {
                        "success": True,
                        "message_id": 987654321,
                        "text": "Message text",
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                },
                "/api/messages/mass-send": {
                    "method": "POST",
                    "description": "Send a message to all chats at once",
                    "auth_required": True,
                    "parameters": {
                        "test_mode": "Test mode - only show recipients (default: false)",
                        "exclude_usernames": "List of usernames to exclude"
                    },
                    "body": {
                        "text": "Message text",
                        "media_ids": [],
                        "price": 0,
                        "locked_text": False
                    },
                    "response": {
                        "total_chats": 100,
                        "successful_sends": 95,
                        "failed_sends": 5,
                        "test_mode": False,
                        "results": []
                    }
                },
                "/api/messages/mass-send/filtered": {
                    "method": "POST",
                    "description": "Send messages to filtered chats with advanced options",
                    "auth_required": True,
                    "parameters": {
                        "only_subscribed": "Only send to subscribed users",
                        "only_active_chats": "Only send to recently active chats",
                        "days_active": "Consider chats active within X days",
                        "test_mode": "Test mode (default: true)",
                        "exclude_usernames": "Usernames to exclude"
                    },
                    "body": {
                        "text": "Message text",
                        "media_ids": [],
                        "price": 0,
                        "locked_text": False
                    },
                    "response": {
                        "total_chats_found": 100,
                        "chats_after_filtering": 50,
                        "successful": 48,
                        "failed": 2,
                        "summary": {}
                    }
                }
            },
            "interactions": {
                "/api/post/{post_id}": {
                    "method": "GET",
                    "description": "Get a specific post by ID",
                    "auth_required": True,
                    "parameters": {"post_id": "Numeric post ID"},
                    "response": {"post": {}, "found": True}
                },
                "/api/post/{post_id}/like": {
                    "method": "POST",
                    "description": "Like a post",
                    "auth_required": True,
                    "parameters": {"post_id": "Numeric post ID"},
                    "response": {"success": True, "liked": True, "post_id": 123456}
                },
                "/api/post/{post_id}/like": {
                    "method": "DELETE",
                    "description": "Unlike a post",
                    "auth_required": True,
                    "parameters": {"post_id": "Numeric post ID"},
                    "response": {"success": True, "liked": False, "post_id": 123456}
                },
                "/api/user/{user_id}/block": {
                    "method": "POST",
                    "description": "Block a user",
                    "auth_required": True,
                    "parameters": {"user_id": "Numeric user ID"},
                    "response": {"success": True, "message": "User blocked successfully"}
                },
                "/api/user/{user_id}/block": {
                    "method": "DELETE",
                    "description": "Unblock a user",
                    "auth_required": True,
                    "parameters": {"user_id": "Numeric user ID"},
                    "response": {"success": True, "message": "User unblocked successfully"}
                }
            },
            "financial": {
                "/api/transactions": {
                    "method": "GET",
                    "description": "Get your transaction history",
                    "auth_required": True,
                    "response": {"transactions": [], "count": 0}
                },
                "/api/paid-content": {
                    "method": "GET",
                    "description": "Get paid content purchases",
                    "auth_required": True,
                    "parameters": {
                        "performer_id": "Filter by specific performer",
                        "limit": "Number of items (default: 10)",
                        "offset": "Pagination offset"
                    },
                    "response": {
                        "paid_content": [{
                            "id": 123456,
                            "type": "message",
                            "text": "Content description",
                            "price": 999,
                            "author": {"id": 789, "username": "creator"},
                            "created_at": "2025-01-01T00:00:00Z"
                        }],
                        "count": 10
                    }
                }
            },
            "vault": {
                "/api/vault": {
                    "method": "GET",
                    "description": "Get media from your vault",
                    "auth_required": True,
                    "parameters": {
                        "limit": "Number of items (default: 50)",
                        "offset": "Pagination offset"
                    },
                    "response": {
                        "vault_media": [{
                            "id": 123456,
                            "type": "photo",
                            "url": "https://...",
                            "preview": "https://...",
                            "created_at": "2025-01-01T00:00:00Z"
                        }],
                        "count": 50
                    }
                }
            },
            "other": {
                "/api/promotions": {
                    "method": "GET",
                    "description": "Get your active promotions (read-only)",
                    "auth_required": True,
                    "response": {
                        "promotions": [{
                            "id": 123,
                            "discount": 50,
                            "price": 499,
                            "duration": 30,
                            "is_active": True,
                            "type": "subscription"
                        }]
                    }
                }
            },
            "debug_testing": {
                "/api/debug/user/{username}/messages": {
                    "method": "GET",
                    "description": "Debug endpoint to see raw message data and identify mass messages",
                    "auth_required": True,
                    "parameters": {
                        "username": "User to analyze",
                        "limit": "Number of messages to check (max: 50)"
                    },
                    "response": {
                        "user": {"id": 123, "username": "username"},
                        "messages_analyzed": 10,
                        "messages": []
                    }
                },
                "/api/test/user/{username}/message-access": {
                    "method": "GET",
                    "description": "Test endpoint to check if you can access messages from a user",
                    "auth_required": True,
                    "parameters": {"username": "User to test"},
                    "response": {
                        "user": {"id": 123, "username": "username"},
                        "tests": {
                            "default_get_messages": {"success": True, "message_count": 50},
                            "has_chat": True,
                            "paid_content": {"success": True, "count": 5}
                        }
                    }
                }
            }
        },
        "notes": [
            "All timestamps are in ISO 8601 format",
            "Prices are in cents (divide by 100 for dollars)",
            "Media URLs are temporary and IP-locked",
            "Rate limits apply - avoid making too many requests",
            "Message pagination uses offset_id, not offset",
            "Post pagination uses label and after_date parameters"
        ]
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
    label: str = Query("", description="Filter by label: archived, private_archived"),
    after_date: float | None = Query(None, description="Unix timestamp to get posts after"),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        posts = await user.get_posts(limit=limit, label=label, after_date=after_date)
        
        posts_data = []
        for post in posts:
            # Handle both dict and PostModel objects
            if isinstance(post, dict):
                post_dict = {
                    "id": post.get('id'),
                    "text": post.get('text', ''),
                    "raw_text": post.get('rawText', ''),
                    "price": post.get('price', 0),
                    "created_at": post.get('postedAt'),
                    "likes_count": post.get('favoritesCount', 0),
                    "comments_count": post.get('commentsCount', 0),
                    "is_pinned": post.get('isPinned', False),
                    "is_archived": post.get('isArchived', False),
                    "is_deleted": post.get('isDeleted', False),
                    "can_comment": post.get('canComment', True),
                    "can_view_media": post.get('canViewMedia', True),
                    "media_count": post.get('mediaCount', 0),
                    "media": []
                }
                media_list = post.get('media', [])
            else:
                # PostModel object
                post_dict = {
                    "id": post.id,
                    "text": post.text,
                    "raw_text": getattr(post, 'rawText', ''),
                    "price": getattr(post, 'price', 0),
                    "created_at": post.created_at.isoformat() if hasattr(post, 'created_at') else None,
                    "likes_count": getattr(post, 'favoritesCount', 0),
                    "comments_count": getattr(post, 'commentsCount', 0),
                    "is_pinned": getattr(post, 'isPinned', False),
                    "is_archived": getattr(post, 'isArchived', False),
                    "is_deleted": getattr(post, 'isDeleted', False),
                    "can_comment": getattr(post, 'canComment', True),
                    "can_view_media": getattr(post, 'canViewMedia', True),
                    "media_count": getattr(post, 'media_count', 0),
                    "media": []
                }
                media_list = getattr(post, 'media', [])
            
            if media_list:
                for media in media_list:
                    if isinstance(media, dict):
                        # Get URL using url_picker if available
                        media_url = None
                        if hasattr(post, 'url_picker') and media.get('canView', False):
                            try:
                                url_result = post.url_picker(media)
                                if url_result:
                                    media_url = url_result.geturl()
                            except:
                                pass
                        
                        post_dict["media"].append({
                            "id": media.get('id'),
                            "type": media.get('type', 'photo'),
                            "url": media_url,
                            "preview": media.get('preview'),
                            "can_view": media.get('canView', False),
                            "is_locked": media.get('isLocked', False),
                            "has_error": media.get('hasError', False)
                        })
                    else:
                        # Media is an object
                        post_dict["media"].append({
                            "id": getattr(media, 'id', None),
                            "type": getattr(media, 'type', 'photo'),
                            "url": getattr(media, 'url', None),
                            "preview": getattr(media, 'preview', None),
                            "can_view": getattr(media, 'canView', True),
                            "is_locked": getattr(media, 'isLocked', False),
                            "has_error": getattr(media, 'hasError', False)
                        })
            
            posts_data.append(post_dict)
        
        return {
            "posts": posts_data,
            "count": len(posts_data),
            "limit": limit,
            "label": label,
            "after_date": after_date
        }
    
    except Exception as e:
        logger.error(f"Get user posts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{username}/messages")
async def get_user_messages(
    username: str = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset_id: int | None = Query(None, description="Message ID to start from"),
    cutoff_id: int | None = Query(None, description="Message ID to stop at"),
    authed_instance=Depends(require_auth)
):
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            messages = await user.get_messages(limit=limit, offset_id=offset_id, cutoff_id=cutoff_id)
        except Exception as msg_error:
            logger.error(f"Error getting messages: {msg_error}")
            logger.exception("Full traceback:")
            raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(msg_error)}")
        
        messages_data = []
        if not messages:
            logger.info(f"No messages found for user {username}")
        
        for i, message in enumerate(messages):
            try:
                # Debug logging (disabled)
                # logger.debug(f"Processing message {i}: type={type(message)}")
                
                # Handle both MessageModel objects and dict responses
                if isinstance(message, dict):
                    # This shouldn't happen with MessageModel, but handle it just in case
                    message_dict = {
                        "id": message.get('id'),
                        "text": message.get('text', ''),
                        "price": message.get('price', 0),
                        "price_dollars": message.get('price', 0) / 100 if message.get('price', 0) else 0,
                        "is_free": message.get('isFree', True),
                        "is_tip": message.get('isTip', False),
                        "is_opened": message.get('isOpened', False),
                        "is_new": message.get('isNew', False),
                        "is_from_queue": message.get('isFromQueue', False),
                        "created_at": message.get('created_at') or message.get('createdAt'),
                        "changed_at": message.get('changedAt'),
                        "media_count": message.get('mediaCount', 0),
                        "preview_count": len(message.get('previews', [])),
                        "is_liked": message.get('isLiked', False),
                        "is_media_ready": message.get('isMediaReady', True),
                        "can_purchase": message.get('canPurchase', False),
                        "locked_text": message.get('lockedText', False),
                        "response_type": message.get('responseType', 'message'),
                        "author": message.get('fromUser', {}),
                        "media": []
                    }
                    
                    media_list = message.get('media', [])
                    if media_list:
                        for media in media_list:
                            message_dict["media"].append({
                                "id": media.get('id'),
                                "type": media.get('type', 'photo'),
                                "url": media.get('url') or media.get('src'),
                                "preview": media.get('preview'),
                                "can_view": media.get('canView', True),
                                "status": "viewable" if media.get('canView', True) else "locked"
                            })
                else:
                    # Handle MessageModel objects
                    message_dict = {
                        "id": message.id,
                        "text": message.text,
                        "price": getattr(message, 'price', 0),
                        "price_dollars": getattr(message, 'price', 0) / 100 if getattr(message, 'price', 0) else 0,
                        "is_free": getattr(message, 'isFree', True),
                        "is_tip": getattr(message, 'isTip', False),
                        "is_opened": getattr(message, 'isOpened', False),
                        "is_new": getattr(message, 'isNew', False),
                        "is_from_queue": getattr(message, 'is_from_queue', False),
                        "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                        "changed_at": getattr(message, 'changedAt', None),
                        "media_count": getattr(message, 'media_count', 0),
                        "preview_count": len(getattr(message, 'previews', [])),
                        "is_liked": getattr(message, 'isLiked', False),
                        "is_media_ready": getattr(message, 'isMediaReady', True),
                        "can_purchase": getattr(message, 'canPurchase', False),
                        "locked_text": getattr(message, 'lockedText', False),
                        "response_type": getattr(message, 'responseType', 'message'),
                        "author": {
                            "id": message.author.id if hasattr(message, 'author') else message.user.id,
                            "username": message.author.username if hasattr(message, 'author') else message.user.username,
                            "name": message.author.name if hasattr(message, 'author') else message.user.name
                        },
                        "media": []
                    }
                    
                    if hasattr(message, 'media') and message.media:
                        for media in message.media:
                            # Media items in MessageModel are dictionaries, not objects
                            if isinstance(media, dict):
                                # Get the actual URL using url_picker
                                media_url = None
                                preview_url = None
                                can_view = media.get('canView', True)
                                
                                if can_view and hasattr(message, 'url_picker'):
                                    try:
                                        url_result = message.url_picker(media)
                                        if url_result:
                                            media_url = url_result.geturl()
                                    except Exception as e:
                                        logger.error(f"Error getting URL with url_picker: {e}")
                                
                                # Try to get preview URL
                                if hasattr(message, 'preview_url_picker'):
                                    try:
                                        preview_result = message.preview_url_picker(media)
                                        if preview_result:
                                            preview_url = preview_result if isinstance(preview_result, str) else preview_result.geturl()
                                    except:
                                        pass
                                
                                message_dict["media"].append({
                                    "id": media.get('id'),
                                    "type": media.get('type', 'photo'),
                                    "url": media_url,
                                    "preview": preview_url,
                                    "thumb": media.get('thumb'),
                                    "source": media.get('source'),
                                    "duration": media.get('duration', 0),
                                    "can_view": can_view,
                                    "has_error": media.get('hasError', False),
                                    "is_locked": media.get('isLocked', False),
                                    "status": "viewable" if can_view else "locked"
                                })
                            else:
                                # In case media is an object
                                message_dict["media"].append({
                                    "id": getattr(media, 'id', None),
                                    "type": getattr(media, 'type', 'photo'),
                                    "url": getattr(media, 'url', None),
                                    "preview": getattr(media, 'preview', None),
                                    "can_view": True,
                                    "status": "viewable"
                                })
            
                # Add media_status if message has media
                if message_dict["media"]:
                    locked_count = sum(1 for m in message_dict["media"] if not m.get("can_view", True))
                    if locked_count == 0:
                        message_dict["media_status"] = "all_viewable"
                    elif locked_count == len(message_dict["media"]):
                        message_dict["media_status"] = "all_locked"
                    else:
                        message_dict["media_status"] = "some_viewable"
                
                messages_data.append(message_dict)
            except Exception as e:
                logger.error(f"Error processing message {i}: {e}")
                logger.error(f"Message type: {type(message)}")
                logger.error(f"Message content: {message}")
                raise
        
        # Calculate statistics
        ppv_messages = sum(1 for msg in messages_data if msg.get('price', 0) > 0)
        locked_media_items = sum(
            sum(1 for media in msg.get('media', []) if not media.get('can_view', True))
            for msg in messages_data
        )
        viewable_media_items = sum(
            sum(1 for media in msg.get('media', []) if media.get('can_view', True))
            for msg in messages_data
        )
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name
            },
            "fetch_date": datetime.now().isoformat(),
            "total_messages": len(messages_data),
            "statistics": {
                "ppv_messages": ppv_messages,
                "locked_media_items": locked_media_items,
                "viewable_media_items": viewable_media_items
            },
            "messages": messages_data
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
    limit: int = Query(100, ge=1, le=200),
    authed_instance=Depends(require_auth)
):
    """
    Get mass messages FROM a specific user (messages they sent to you)
    Mass messages are identified by isFromQueue=True or having a queue_id
    """
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get all messages from this user
        messages = []
        try:
            logger.info(f"Fetching messages for user {username} (ID: {user.id}) with limit={limit}")
            messages = await user.get_messages(limit=limit, cutoff_id=message_cutoff_id)
            logger.info(f"Retrieved {len(messages)} messages")
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            # Try without cutoff_id if it fails
            try:
                messages = await user.get_messages(limit=limit)
                logger.info(f"Retrieved {len(messages)} messages without cutoff_id")
            except Exception as e2:
                logger.error(f"Error getting messages (retry): {e2}")
        
        # Also check paid content messages
        paid_messages = []
        try:
            paid_content = await user.get_paid_contents()
            paid_messages = [
                x for x in paid_content 
                if hasattr(x, 'is_mass_message') and callable(x.is_mass_message)
            ]
            logger.info(f"Found {len(paid_messages)} paid messages with is_mass_message method")
        except Exception as e:
            logger.warning(f"Could not get paid content: {e}")
        
        # Filter for mass messages FROM this user
        mass_messages_data = []
        total_checked = 0
        
        for message in messages + paid_messages:
            total_checked += 1
            try:
                # Check if it's a mass message
                is_mass = False
                queue_info = {}
                
                if hasattr(message, 'is_mass_message') and callable(message.is_mass_message):
                    is_mass = message.is_mass_message()
                elif hasattr(message, 'isFromQueue'):
                    is_mass = bool(message.isFromQueue)
                elif hasattr(message, 'queue_id'):
                    is_mass = message.queue_id is not None
                
                # Also check raw data
                if hasattr(message, '__raw__'):
                    raw = message.__raw__
                    if raw.get('isFromQueue') or raw.get('queueId'):
                        is_mass = True
                        queue_info = {
                            "queue_id": raw.get('queueId'),
                            "is_from_queue": raw.get('isFromQueue', False),
                            "can_unsend_queue": raw.get('canUnsendQueue', False)
                        }
                
                if is_mass:
                    # Make sure the message is FROM the user we're querying
                    author_id = None
                    if hasattr(message, 'author') and hasattr(message.author, 'id'):
                        author_id = message.author.id
                    elif hasattr(message, 'fromUser') and hasattr(message.fromUser, 'id'):
                        author_id = message.fromUser.id
                    
                    if author_id == user.id:
                        mass_messages_data.append({
                            "id": message.id,
                            "text": getattr(message, 'text', ''),
                            "price": getattr(message, 'price', 0),
                            "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                            "is_mass_message": True,
                            "is_opened": getattr(message, 'isOpened', False),
                            "is_new": getattr(message, 'isNew', False),
                            "media_count": getattr(message, 'media_count', 0),
                            "queue_info": queue_info
                        })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
        
        return {
            "mass_messages": mass_messages_data,
            "count": len(mass_messages_data),
            "total_messages_checked": total_checked,
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name
            }
        }
    
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
    sub_type: str = Query("all", description="Type of subscriptions (all, active, expired, attention)"),
    filter_by: str = Query("", description="Filter subscriptions by specific value"),
    authed_instance=Depends(require_auth)
):
    try:
        subscriptions = await authed_instance.get_subscriptions(limit=limit, sub_type=sub_type, filter_by=filter_by)
        
        subscriptions_data = []
        for subscription in subscriptions:
            try:
                # Check if subscription has user attribute (SubscriptionModel)
                if hasattr(subscription, 'user') and subscription.user:
                    user = subscription.user
                    subscription_data = {
                        "id": user.id,
                        "username": user.username,
                        "name": user.name,
                        "avatar": getattr(user, 'avatar', None),
                        "subscription_price": subscription.subscribe_price if hasattr(subscription, 'subscribe_price') else 0,
                        "is_active": subscription.is_active() if hasattr(subscription, 'is_active') and callable(subscription.is_active) else subscription.active,
                        "expire_date": subscription.subscribed_by_expire_date.isoformat() if hasattr(subscription, 'subscribed_by_expire_date') else None,
                        "current_price": subscription.current_subscribe_price if hasattr(subscription, 'current_subscribe_price') else 0
                    }
                else:
                    # Fallback for other subscription formats
                    subscription_data = {
                        "id": getattr(subscription, 'id', None),
                        "username": getattr(subscription, 'username', None),
                        "name": getattr(subscription, 'name', None),
                        "avatar": getattr(subscription, 'avatar', None),
                        "subscription_price": getattr(subscription, 'subscription_price', 0),
                        "is_active": getattr(subscription, 'is_active', False)
                    }
                subscriptions_data.append(subscription_data)
            except Exception as e:
                logger.error(f"Error processing subscription: {e}")
                logger.error(f"Subscription type: {type(subscription)}")
                continue
        
        return {
            "subscriptions": subscriptions_data,
            "count": len(subscriptions_data),
            "limit": limit,
            "sub_type": sub_type,
            "filter_by": filter_by
        }
    
    except Exception as e:
        logger.error(f"Get subscriptions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages/all/detailed")
async def get_all_messages_detailed(
    limit_per_chat: int = Query(100, ge=1, le=200, description="Max messages per chat"),
    include_purchases: bool = Query(True, description="Include PPV purchases"),
    include_tips: bool = Query(True, description="Include tip messages"),
    only_with_media: bool = Query(False, description="Only messages with media"),
    authed_instance=Depends(require_auth)
):
    """
    Get all messages from all chats with detailed statistics and filtering
    """
    try:
        logger.info("Fetching detailed messages from all chats")
        
        # First get all chats
        chats = await authed_instance.get_chats(limit=200, offset=0)
        
        all_messages = []
        chat_details = {}
        statistics = {
            "total_messages": 0,
            "total_chats": 0,
            "ppv_messages": 0,
            "tip_messages": 0,
            "free_messages": 0,
            "messages_with_media": 0,
            "total_spent": 0
        }
        
        for chat in chats:
            try:
                # Get user info from chat
                if hasattr(chat, 'user') and chat.user:
                    user = chat.user
                    user_id = user.id
                    username = user.username
                    name = user.name
                    
                    logger.info(f"Processing chat with {username}")
                    
                    # Initialize chat details
                    if username not in chat_details:
                        chat_details[username] = {
                            "user_id": user_id,
                            "username": username,
                            "name": name,
                            "message_count": 0,
                            "ppv_count": 0,
                            "tip_count": 0,
                            "media_count": 0,
                            "total_spent": 0,
                            "last_message_date": None,
                            "first_message_date": None
                        }
                    
                    # Get messages for this user
                    messages = await user.get_messages(limit=limit_per_chat)
                    
                    for message in messages:
                        try:
                            # Handle both dict and MessageModel objects
                            if isinstance(message, dict):
                                message_data = message
                            else:
                                # Convert MessageModel to dict-like structure
                                message_data = {
                                    "id": message.id,
                                    "text": message.text,
                                    "price": message.price if hasattr(message, 'price') else 0,
                                    "isFree": message.isFree if hasattr(message, 'isFree') else True,
                                    "isTip": message.isTip if hasattr(message, 'isTip') else False,
                                    "isOpened": message.isOpened if hasattr(message, 'isOpened') else True,
                                    "isNew": message.isNew if hasattr(message, 'isNew') else False,
                                    "media_count": message.media_count if hasattr(message, 'media_count') else 0,
                                    "created_at": message.created_at if hasattr(message, 'created_at') else None,
                                    "author": message.author if hasattr(message, 'author') else None,
                                    "media": message.media if hasattr(message, 'media') else []
                                }
                            
                            # Apply filters
                            price = message_data.get('price', 0) or 0
                            is_tip = message_data.get('isTip', False)
                            is_free = message_data.get('isFree', True)
                            media_count = message_data.get('media_count', 0)
                            
                            # Skip based on filters
                            if not include_purchases and price > 0 and not is_tip:
                                continue
                            if not include_tips and is_tip:
                                continue
                            if only_with_media and media_count == 0:
                                continue
                            
                            # Build message dict
                            message_dict = {
                                "id": message_data.get('id'),
                                "text": message_data.get('text', ''),
                                "price": price,
                                "price_dollars": price / 100 if price else 0,
                                "is_free": is_free,
                                "is_tip": is_tip,
                                "is_opened": message_data.get('isOpened', True),
                                "is_new": message_data.get('isNew', False),
                                "media_count": media_count,
                                "created_at": None,
                                "chat_user": {
                                    "id": user_id,
                                    "username": username,
                                    "name": name
                                }
                            }
                            
                            # Handle created_at
                            if message_data.get('created_at'):
                                if hasattr(message_data['created_at'], 'isoformat'):
                                    message_dict["created_at"] = message_data['created_at'].isoformat()
                                else:
                                    message_dict["created_at"] = str(message_data['created_at'])
                            
                            # Handle author
                            if message_data.get('author'):
                                author = message_data['author']
                                if hasattr(author, 'id'):
                                    message_dict["author"] = {
                                        "id": author.id,
                                        "username": author.username if hasattr(author, 'username') else None
                                    }
                                    message_dict["is_from_me"] = (author.id == authed_instance.id)
                                else:
                                    message_dict["is_from_me"] = False
                            
                            # Handle media with url_picker
                            if message_data.get('media') and hasattr(message, 'url_picker'):
                                message_dict["media"] = []
                                for media in message_data['media']:
                                    if isinstance(media, dict):
                                        media_url = None
                                        if media.get('canView', False):
                                            try:
                                                url_result = message.url_picker(media)
                                                if url_result:
                                                    media_url = url_result.geturl()
                                            except:
                                                pass
                                        
                                        message_dict["media"].append({
                                            "id": media.get('id'),
                                            "type": media.get('type', 'photo'),
                                            "url": media_url,
                                            "can_view": media.get('canView', False),
                                            "is_locked": media.get('isLocked', False)
                                        })
                            
                            # Update statistics
                            statistics["total_messages"] += 1
                            if price > 0:
                                if is_tip:
                                    statistics["tip_messages"] += 1
                                else:
                                    statistics["ppv_messages"] += 1
                                statistics["total_spent"] += price
                            else:
                                statistics["free_messages"] += 1
                            
                            if media_count > 0:
                                statistics["messages_with_media"] += 1
                            
                            # Update chat details
                            chat_details[username]["message_count"] += 1
                            if price > 0:
                                chat_details[username]["total_spent"] += price
                                if is_tip:
                                    chat_details[username]["tip_count"] += 1
                                else:
                                    chat_details[username]["ppv_count"] += 1
                            
                            if media_count > 0:
                                chat_details[username]["media_count"] += 1
                            
                            # Track dates
                            if message_dict["created_at"]:
                                if not chat_details[username]["last_message_date"] or message_dict["created_at"] > chat_details[username]["last_message_date"]:
                                    chat_details[username]["last_message_date"] = message_dict["created_at"]
                                if not chat_details[username]["first_message_date"] or message_dict["created_at"] < chat_details[username]["first_message_date"]:
                                    chat_details[username]["first_message_date"] = message_dict["created_at"]
                            
                            all_messages.append(message_dict)
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue
                    
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                continue
        
        # Sort messages by created_at (newest first)
        all_messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Convert chat_details to list and sort by message count
        chat_list = list(chat_details.values())
        chat_list.sort(key=lambda x: x['message_count'], reverse=True)
        
        statistics["total_chats"] = len(chat_list)
        statistics["total_spent_dollars"] = statistics["total_spent"] / 100
        
        return {
            "statistics": statistics,
            "chats": chat_list,
            "messages": all_messages
        }
    
    except Exception as e:
        logger.error(f"Get all messages detailed error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages/all")
async def get_all_messages(
    limit_per_chat: int = Query(50, ge=1, le=100, description="Max messages per chat"),
    include_purchases: bool = Query(True, description="Include PPV purchases"),
    authed_instance=Depends(require_auth)
):
    """
    Get all messages from all chats
    """
    try:
        logger.info("Fetching all messages from all chats")
        
        # First get all chats
        chats = await authed_instance.get_chats(limit=100, offset=0)
        
        all_messages = []
        chat_summaries = []
        total_message_count = 0
        
        for chat in chats:
            try:
                # Get user info from chat
                if hasattr(chat, 'user') and chat.user:
                    user = chat.user
                    user_id = user.id
                    username = user.username
                    name = user.name
                    
                    logger.info(f"Fetching messages from chat with {username}")
                    
                    # Get messages for this user
                    messages = await user.get_messages(limit=limit_per_chat)
                    
                    chat_message_count = 0
                    
                    for message in messages:
                        # Process each message similar to the messages endpoint
                        try:
                            # Handle both dict and MessageModel objects
                            if isinstance(message, dict):
                                message_dict = {
                                    "id": message.get('id'),
                                    "text": message.get('text', ''),
                                    "price": message.get('price', 0),
                                    "price_dollars": message.get('price', 0) / 100 if message.get('price', 0) else 0,
                                    "is_free": message.get('isFree', True),
                                    "is_tip": message.get('isTip', False),
                                    "is_opened": message.get('isOpened', True),
                                    "is_new": message.get('isNew', False),
                                    "is_from_queue": message.get('isFromQueue', False),
                                    "queue_id": message.get('queue_id'),
                                    "can_be_pinned": message.get('canBePinned', False),
                                    "can_purchase": message.get('canPurchase', False),
                                    "can_purchase_reason": message.get('canPurchaseReason'),
                                    "can_unsend": message.get('canUnsend', False),
                                    "can_be_favorited": message.get('canBeFavorited', False),
                                    "can_be_tipped": message.get('canBeTipped', False),
                                    "can_report": message.get('canReport', False),
                                    "locked_text": message.get('lockedText', False),
                                    "has_opened": message.get('hasOpened', False),
                                    "is_liked": message.get('isLiked', False),
                                    "is_media_ready": message.get('isMediaReady', True),
                                    "is_performer": message.get('isPerformer', False),
                                    "is_forward": message.get('isForward', False),
                                    "is_pinned": message.get('isPinned', False),
                                    "giphy_id": message.get('giphyId'),
                                    "product_id": message.get('productId'),
                                    "response_type": message.get('responseType', 'message'),
                                    "notification_type": message.get('notificationType'),
                                    "reply_on_message_id": message.get('replyOnMessageId'),
                                    "created_at": message.get('createdAt') or message.get('created_at'),
                                    "changed_at": message.get('changedAt'),
                                    "media_count": message.get('mediaCount', 0),
                                    "preview_count": len(message.get('previews', [])),
                                    "previews": message.get('previews', []),
                                    "attachments": message.get('attachments', []),
                                    "chat_user": {
                                        "id": user_id,
                                        "username": username,
                                        "name": name
                                    },
                                    "author": message.get('fromUser', {}) or message.get('author', {}),
                                    "_raw": message
                                }
                            else:
                                # MessageModel object - include ALL message fields
                                message_dict = {
                                    "id": message.id,
                                    "text": message.text,
                                    "price": message.price if hasattr(message, 'price') else 0,
                                    "price_dollars": message.price / 100 if hasattr(message, 'price') and message.price else 0,
                                    "is_free": message.isFree if hasattr(message, 'isFree') else True,
                                    "is_tip": message.isTip if hasattr(message, 'isTip') else False,
                                    "is_opened": message.isOpened if hasattr(message, 'isOpened') else True,
                                    "is_new": message.isNew if hasattr(message, 'isNew') else False,
                                    "is_from_queue": getattr(message, 'isFromQueue', False),
                                    "queue_id": getattr(message, 'queue_id', None),
                                    "can_be_pinned": getattr(message, 'canBePinned', False),
                                    "can_purchase": getattr(message, 'canPurchase', False),
                                    "can_purchase_reason": getattr(message, 'canPurchaseReason', None),
                                    "can_unsend": getattr(message, 'canUnsend', False),
                                    "can_be_favorited": getattr(message, 'canBeFavorited', False),
                                    "can_be_tipped": getattr(message, 'canBeTipped', False),
                                    "can_report": getattr(message, 'canReport', False),
                                    "locked_text": getattr(message, 'lockedText', False),
                                    "has_opened": getattr(message, 'hasOpened', False),
                                    "is_liked": getattr(message, 'isLiked', False),
                                    "is_media_ready": getattr(message, 'isMediaReady', True),
                                    "is_performer": getattr(message, 'isPerformer', False),
                                    "is_forward": getattr(message, 'isForward', False),
                                    "is_pinned": getattr(message, 'isPinned', False),
                                    "giphy_id": getattr(message, 'giphyId', None),
                                    "product_id": getattr(message, 'productId', None),
                                    "response_type": getattr(message, 'responseType', 'message'),
                                    "notification_type": getattr(message, 'notificationType', None),
                                    "reply_on_message_id": getattr(message, 'replyOnMessageId', None),
                                    "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') and message.created_at else None,
                                    "changed_at": getattr(message, 'changedAt', None),
                                    "media_count": message.media_count if hasattr(message, 'media_count') else 0,
                                    "preview_count": len(getattr(message, 'previews', [])),
                                    "previews": getattr(message, 'previews', []),
                                    "attachments": getattr(message, 'attachments', []),
                                    "chat_user": {
                                        "id": user_id,
                                        "username": username,
                                        "name": name
                                    },
                                    "author": {
                                        "id": message.author.id if hasattr(message, 'author') and message.author else None,
                                        "username": message.author.username if hasattr(message, 'author') and message.author else None,
                                        "name": message.author.name if hasattr(message, 'author') and message.author else None
                                    },
                                    # Include raw data if available
                                    "_raw": getattr(message, '_data', None)
                                }
                                
                                # Add media if available
                                if hasattr(message, 'media') and message.media:
                                    message_dict["media"] = []
                                    for media in message.media:
                                        if isinstance(media, dict):
                                            # Get URL using url_picker if available
                                            media_url = None
                                            if hasattr(message, 'url_picker') and media.get('canView', False):
                                                try:
                                                    url_result = message.url_picker(media)
                                                    if url_result:
                                                        media_url = url_result.geturl()
                                                except:
                                                    pass
                                            
                                            message_dict["media"].append({
                                                "id": media.get('id'),
                                                "type": media.get('type', 'photo'),
                                                "url": media_url,
                                                "can_view": media.get('canView', False)
                                            })
                            
                            # Only include PPV messages if requested
                            if not include_purchases and message_dict.get('price', 0) > 0:
                                continue
                                
                            all_messages.append(message_dict)
                            chat_message_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue
                    
                    # Add chat summary
                    chat_summaries.append({
                        "user_id": user_id,
                        "username": username,
                        "name": name,
                        "message_count": chat_message_count
                    })
                    
                    total_message_count += chat_message_count
                    
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                continue
        
        # Sort messages by created_at (newest first)
        all_messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "total_messages": total_message_count,
            "total_chats": len(chat_summaries),
            "chat_summaries": chat_summaries,
            "messages": all_messages
        }
    
    except Exception as e:
        logger.error(f"Get all messages error: {str(e)}")
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
            try:
                # ChatModel stores user info in the 'user' attribute
                if hasattr(chat, 'user') and chat.user:
                    user = chat.user
                    chat_data = {
                        "id": user.id,
                        "username": user.username,
                        "name": user.name,
                        "avatar": getattr(user, 'avatar', None),
                        "has_purchased_feed": chat.has_purchased_feed if hasattr(chat, 'has_purchased_feed') else False,
                        "count_pinned_messages": chat.count_pinned_messages if hasattr(chat, 'count_pinned_messages') else 0,
                        "last_read_message_id": chat.last_read_message_id if hasattr(chat, 'last_read_message_id') else None
                    }
                    
                    # Add last message info if available
                    if hasattr(chat, 'last_message') and chat.last_message:
                        last_msg = chat.last_message
                        chat_data["last_message"] = {
                            "id": last_msg.id,
                            "text": last_msg.text,
                            "created_at": last_msg.created_at.isoformat() if hasattr(last_msg, 'created_at') else None,
                            "is_from_user": last_msg.author.id == user.id if hasattr(last_msg, 'author') else False
                        }
                    else:
                        chat_data["last_message"] = None
                else:
                    # Fallback for other chat formats
                    chat_data = {
                        "id": getattr(chat, 'id', None),
                        "username": getattr(chat, 'username', None),
                        "name": getattr(chat, 'name', None),
                        "avatar": getattr(chat, 'avatar', None),
                        "last_message": getattr(chat, 'last_message', None),
                        "unread_count": getattr(chat, 'unread_count', 0)
                    }
                
                chats_data.append(chat_data)
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                logger.error(f"Chat type: {type(chat)}")
                continue
        
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
@app.post("/api/messages/mass-send")
async def mass_send_message(
    request: MassMessageRequest,
    test_mode: bool = Query(False, description="Test mode - only show who would receive the message"),
    exclude_usernames: list[str] = Query([], description="Usernames to exclude from mass send"),
    authed_instance=Depends(require_auth)
):
    """
    Send a message to all chats at once
    """
    try:
        logger.info(f"Mass sending message to all chats (test_mode={test_mode})")
        
        # Validate request
        if not request.text and not request.media_ids:
            raise HTTPException(status_code=400, detail="Either text or media_ids must be provided")
        
        # Get all chats
        chats = await authed_instance.get_chats(limit=200, offset=0)
        
        results = {
            "total_chats": 0,
            "successful_sends": 0,
            "failed_sends": 0,
            "test_mode": test_mode,
            "results": []
        }
        
        for chat in chats:
            try:
                if hasattr(chat, 'user') and chat.user:
                    user = chat.user
                    username = user.username
                    
                    # Skip if username is in exclude list
                    if username in exclude_usernames:
                        results["results"].append({
                            "username": username,
                            "status": "skipped",
                            "reason": "Username in exclude list"
                        })
                        continue
                    
                    results["total_chats"] += 1
                    
                    if test_mode:
                        # In test mode, just show who would receive the message
                        results["results"].append({
                            "username": username,
                            "user_id": user.id,
                            "name": user.name,
                            "status": "would_send",
                            "message": {
                                "text": request.text,
                                "price": request.price,
                                "media_ids": request.media_ids,
                                "locked_text": request.locked_text
                            }
                        })
                        results["successful_sends"] += 1
                    else:
                        # Actually send the message
                        try:
                            result = await user.send_message(
                                text=request.text,
                                price=request.price,
                                media_ids=request.media_ids,
                                locked_text=request.locked_text
                            )
                            
                            if result:
                                results["successful_sends"] += 1
                                results["results"].append({
                                    "username": username,
                                    "user_id": user.id,
                                    "status": "success",
                                    "message_id": result.id if hasattr(result, 'id') else None
                                })
                            else:
                                results["failed_sends"] += 1
                                results["results"].append({
                                    "username": username,
                                    "user_id": user.id,
                                    "status": "failed",
                                    "reason": "No response from send_message"
                                })
                                
                        except Exception as e:
                            results["failed_sends"] += 1
                            results["results"].append({
                                "username": username,
                                "user_id": user.id,
                                "status": "failed",
                                "error": str(e)
                            })
                            logger.error(f"Failed to send message to {username}: {e}")
                    
                    # Add small delay between sends to avoid rate limiting
                    if not test_mode and results["total_chats"] < len(chats) - 1:
                        await asyncio.sleep(0.5)
                        
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                results["failed_sends"] += 1
                results["results"].append({
                    "status": "failed",
                    "error": f"Chat processing error: {str(e)}"
                })
        
        # Add summary
        results["summary"] = {
            "total_recipients": results["total_chats"],
            "successful": results["successful_sends"],
            "failed": results["failed_sends"],
            "excluded": len(exclude_usernames),
            "success_rate": f"{(results['successful_sends'] / results['total_chats'] * 100):.1f}%" if results['total_chats'] > 0 else "0%"
        }
        
        return results
    
    except Exception as e:
        logger.error(f"Mass send message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/messages/mass-send/filtered")
async def mass_send_message_filtered(
    request: MassMessageRequest,
    only_subscribed: bool = Query(False, description="Only send to users you're subscribed to"),
    only_active_chats: bool = Query(False, description="Only send to chats with recent activity"),
    days_active: int = Query(30, description="Consider chats active if they have messages within X days"),
    test_mode: bool = Query(True, description="Test mode - only show who would receive the message"),
    exclude_usernames: list[str] = Query([], description="Usernames to exclude from mass send"),
    authed_instance=Depends(require_auth)
):
    """
    Send a message to filtered chats with more control
    """
    try:
        logger.info(f"Mass sending filtered message (test_mode={test_mode})")
        
        # Validate request
        if not request.text and not request.media_ids:
            raise HTTPException(status_code=400, detail="Either text or media_ids must be provided")
        
        # Get all chats
        chats = await authed_instance.get_chats(limit=200, offset=0)
        
        # Get subscriptions if filtering by subscribed
        subscribed_users = set()
        if only_subscribed:
            subscriptions = await authed_instance.get_subscriptions(limit=200)
            for sub in subscriptions:
                if hasattr(sub, 'user') and sub.user:
                    subscribed_users.add(sub.user.username)
        
        results = {
            "total_chats": len(chats),
            "filtered_chats": 0,
            "successful_sends": 0,
            "failed_sends": 0,
            "test_mode": test_mode,
            "filters_applied": {
                "only_subscribed": only_subscribed,
                "only_active_chats": only_active_chats,
                "days_active": days_active if only_active_chats else None,
                "excluded_usernames": exclude_usernames
            },
            "results": []
        }
        
        # Calculate cutoff date for active chats
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_active)
        
        for chat in chats:
            try:
                if hasattr(chat, 'user') and chat.user:
                    user = chat.user
                    username = user.username
                    
                    # Apply filters
                    skip_reasons = []
                    
                    # Check exclude list
                    if username in exclude_usernames:
                        skip_reasons.append("Username in exclude list")
                    
                    # Check subscription filter
                    if only_subscribed and username not in subscribed_users:
                        skip_reasons.append("Not subscribed to user")
                    
                    # Check activity filter
                    if only_active_chats and hasattr(chat, 'last_message') and chat.last_message:
                        if hasattr(chat.last_message, 'created_at'):
                            if chat.last_message.created_at < cutoff_date:
                                skip_reasons.append(f"No activity in last {days_active} days")
                    elif only_active_chats and not hasattr(chat, 'last_message'):
                        skip_reasons.append("No message history")
                    
                    # Skip if any filters failed
                    if skip_reasons:
                        results["results"].append({
                            "username": username,
                            "status": "filtered_out",
                            "reasons": skip_reasons
                        })
                        continue
                    
                    results["filtered_chats"] += 1
                    
                    if test_mode:
                        # In test mode, show who would receive the message
                        results["results"].append({
                            "username": username,
                            "user_id": user.id,
                            "name": user.name,
                            "status": "would_send",
                            "last_activity": chat.last_message.created_at.isoformat() if hasattr(chat, 'last_message') and chat.last_message and hasattr(chat.last_message, 'created_at') else None,
                            "is_subscribed": username in subscribed_users if only_subscribed else None,
                            "message": {
                                "text": request.text,
                                "price": request.price,
                                "media_ids": request.media_ids,
                                "locked_text": request.locked_text
                            }
                        })
                        results["successful_sends"] += 1
                    else:
                        # Actually send the message
                        try:
                            result = await user.send_message(
                                text=request.text,
                                price=request.price,
                                media_ids=request.media_ids,
                                locked_text=request.locked_text
                            )
                            
                            if result:
                                results["successful_sends"] += 1
                                results["results"].append({
                                    "username": username,
                                    "user_id": user.id,
                                    "status": "success",
                                    "message_id": result.id if hasattr(result, 'id') else None
                                })
                            else:
                                results["failed_sends"] += 1
                                results["results"].append({
                                    "username": username,
                                    "user_id": user.id,
                                    "status": "failed",
                                    "reason": "No response from send_message"
                                })
                                
                        except Exception as e:
                            results["failed_sends"] += 1
                            results["results"].append({
                                "username": username,
                                "user_id": user.id,
                                "status": "failed",
                                "error": str(e)
                            })
                            logger.error(f"Failed to send message to {username}: {e}")
                        
                        # Add delay between sends to avoid rate limiting
                        if results["filtered_chats"] < len(chats):
                            await asyncio.sleep(1)  # Longer delay for safety
                            
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                results["results"].append({
                    "status": "failed",
                    "error": f"Chat processing error: {str(e)}"
                })
        
        # Add summary
        results["summary"] = {
            "total_chats_found": results["total_chats"],
            "chats_after_filtering": results["filtered_chats"],
            "successful": results["successful_sends"],
            "failed": results["failed_sends"],
            "filtered_out": results["total_chats"] - results["filtered_chats"],
            "success_rate": f"{(results['successful_sends'] / results['filtered_chats'] * 100):.1f}%" if results['filtered_chats'] > 0 else "0%"
        }
        
        return results
    
    except Exception as e:
        logger.error(f"Mass send filtered message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
@app.get("/api/post/{post_id}")
async def get_post(post_id: int = Path(...), authed_instance=Depends(require_auth)):
    """
    Get a specific post by ID
    """
    try:
        # Try to get the post
        link = f"https://onlyfans.com/api2/v2/posts/{post_id}"
        result = await authed_instance.session_manager.json_request(link)
        
        if isinstance(result, dict) and result.get('error'):
            error_info = result.get('error', {})
            error_code = error_info.get('code', 404)
            error_message = error_info.get('message', 'Post not found')
            raise HTTPException(status_code=error_code, detail=error_message)
        
        return {
            "post": result,
            "found": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get post error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/post/{post_id}/like")
async def like_post(post_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        # Find the post first to get its category
        # For now, assume it's a post (you might need to enhance this)
        # Log the authenticated user ID for debugging
        logger.info(f"Authenticated user ID: {authed_instance.id}")
        logger.info(f"Authenticated username: {authed_instance.username}")
        
        result = await authed_instance.user.like("posts", post_id)
        
        # Log the result for debugging
        logger.info(f"Like result for post {post_id}: {result}")
        
        # Check if the API returned an error
        if isinstance(result, dict) and result.get('error'):
            error_info = result.get('error', {})
            error_code = error_info.get('code', 400)
            error_message = error_info.get('message', 'Like operation failed')
            
            if error_code == 404:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Post {post_id} not found. It may have been deleted or you don't have access to it."
                )
            else:
                raise HTTPException(status_code=error_code, detail=error_message)
        
        return {
            "success": True, 
            "liked": True,
            "post_id": post_id,
            "api_response": result
        }
    
    except Exception as e:
        logger.error(f"Like post error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/post/{post_id}/like")
async def unlike_post(post_id: int = Path(...), authed_instance=Depends(require_auth)):
    try:
        result = await authed_instance.user.unlike("posts", post_id)
        
        # Log the result for debugging
        logger.info(f"Unlike result for post {post_id}: {result}")
        
        # Check if the API returned an error
        if isinstance(result, dict) and result.get('error'):
            error_info = result.get('error', {})
            error_code = error_info.get('code', 400)
            error_message = error_info.get('message', 'Unlike operation failed')
            
            if error_code == 404:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Post {post_id} not found. It may have been deleted or you don't have access to it."
                )
            else:
                raise HTTPException(status_code=error_code, detail=error_message)
        
        return {
            "success": True, 
            "liked": False,
            "post_id": post_id,
            "api_response": result
        }
    
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

# Debug Endpoints
@app.get("/api/debug/user/{username}/messages")
async def debug_user_messages(
    username: str = Path(...),
    limit: int = Query(10, ge=1, le=50),
    authed_instance=Depends(require_auth)
):
    """
    Debug endpoint to see raw message data and identify mass messages
    """
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        messages = await user.get_messages(limit=limit)
        
        debug_data = []
        for i, message in enumerate(messages):
            msg_debug = {
                "index": i,
                "id": message.id,
                "text": getattr(message, 'text', '')[:100] + "...",
                "price": getattr(message, 'price', 0),
                "is_from_queue": getattr(message, 'isFromQueue', None),
                "is_from_queue_raw": message.__raw__.get('isFromQueue') if hasattr(message, '__raw__') else None,
                "queue_id": getattr(message, 'queue_id', None),
                "queue_id_raw": message.__raw__.get('queueId') if hasattr(message, '__raw__') else None,
                "author_id": message.author.id if hasattr(message, 'author') else None,
                "author_username": message.author.username if hasattr(message, 'author') else None,
                "is_mass_message_method": message.is_mass_message() if hasattr(message, 'is_mass_message') and callable(message.is_mass_message) else None,
                "raw_keys": list(message.__raw__.keys()) if hasattr(message, '__raw__') else []
            }
            
            # Check for any queue-related fields in raw data
            if hasattr(message, '__raw__'):
                queue_fields = {k: v for k, v in message.__raw__.items() if 'queue' in k.lower()}
                if queue_fields:
                    msg_debug["queue_related_fields"] = queue_fields
            
            debug_data.append(msg_debug)
        
        return {
            "user": {
                "id": user.id,
                "username": user.username
            },
            "messages_analyzed": len(debug_data),
            "messages": debug_data
        }
    
    except Exception as e:
        logger.error(f"Debug messages error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test/user/{username}/message-access")
async def test_message_access(
    username: str = Path(...),
    authed_instance=Depends(require_auth)
):
    """
    Test endpoint to check if we can access messages from a user
    """
    try:
        user = await authed_instance.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        results = {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name
            },
            "tests": {}
        }
        
        # Test 1: Try to get messages with default parameters
        try:
            messages = await user.get_messages()
            results["tests"]["default_get_messages"] = {
                "success": True,
                "message_count": len(messages),
                "first_message": messages[0].text[:50] if messages else None
            }
        except Exception as e:
            results["tests"]["default_get_messages"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 2: Try with explicit limit
        try:
            messages = await user.get_messages(limit=5)
            results["tests"]["with_limit"] = {
                "success": True,
                "message_count": len(messages)
            }
        except Exception as e:
            results["tests"]["with_limit"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 3: Check if we have chat relationship
        try:
            chats = await authed_instance.get_chats(limit=200)
            has_chat = any(
                chat.user.username == username 
                for chat in chats 
                if hasattr(chat, 'user') and chat.user
            )
            results["tests"]["has_chat"] = has_chat
        except Exception as e:
            results["tests"]["has_chat"] = f"Error: {str(e)}"
        
        # Test 4: Try to get paid content
        try:
            paid_content = await user.get_paid_contents()
            results["tests"]["paid_content"] = {
                "success": True,
                "count": len(paid_content) if isinstance(paid_content, list) else 0
            }
        except Exception as e:
            results["tests"]["paid_content"] = {
                "success": False,
                "error": str(e)
            }
        
        return results
    
    except Exception as e:
        logger.error(f"Test message access error: {str(e)}")
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