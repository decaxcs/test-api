# UltimaScraperAPI - Complete API Endpoint Mapping

This document provides a comprehensive mapping of all Python API functions to their corresponding OnlyFans API endpoints, including parameters, return values, and usage examples.

## Table of Contents
- [Authentication Endpoints](#1-authentication-endpoints)
- [User Profile Endpoints](#2-user-profile-endpoints)
- [Content Fetching Endpoints](#3-content-fetching-endpoints)
- [Messaging Endpoints](#4-messaging-endpoints)
- [Subscription Endpoints](#5-subscription-endpoints)
- [Chat and Communication Endpoints](#6-chat-and-communication-endpoints)
- [Payment and Transaction Endpoints](#7-payment-and-transaction-endpoints)
- [List Management Endpoints](#8-list-management-endpoints)
- [Vault Management Endpoints](#9-vault-management-endpoints)
- [Interaction Endpoints](#10-interaction-endpoints)
- [DRM and Media Protection Endpoints](#11-drm-and-media-protection-endpoints)
- [Usage Patterns](#key-usage-patterns)

---

## 1. Authentication Endpoints

### Login/Authentication Check
```python
# Python Method
await authenticator.login()

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/me

# Headers Required
- Cookie: auth_id=xxx; sess=xxx; ...
- X-BC: xxx
- User-Agent: Mozilla/5.0...

# Returns
{
  "id": 123456,
  "username": "user123",
  "email": "user@email.com",
  "isAuth": true
}

# Usage Example
authed = await api.login(auth_json)
```

### Two-Factor Authentication
```python
# Python Method
await authenticator.submit_2fa_code(code)

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/users/otp/check

# Request Body
{
  "code": "123456",
  "rememberMe": true
}

# Returns
{
  "success": true
}
```

### Login Issues Check
```python
# Python Method
await authed.get_login_issues()

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/issues/login

# Returns
{
  "data": null  # or issue details
}
```

---

## 2. User Profile Endpoints

### Get User by Username/ID
```python
# Python Method
user = await authed.get_user("username")
# or
user = await authed.get_user(123456)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/{identifier}

# Parameters
- identifier: username (string) or user_id (int)

# Returns
{
  "id": 123456,
  "username": "modelname",
  "name": "Model Name",
  "about": "Bio text",
  "avatar": "https://...",
  "header": "https://...",
  "postsCount": 500,
  "photosCount": 400,
  "videosCount": 100,
  "subscribersCount": 1000,
  "subscribedByData": {...},
  "subscribedOnData": {...}
}

# Usage Example
user = await authed.get_user("modelname")
print(f"User: {user.name} has {user.posts_count} posts")
```

### Get Multiple Users
```python
# Python Method
users = await authed.get_users(["user1", "user2", 123456])

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/list?{params}

# URL Parameters
- n[]: user1
- n[]: user2  
- n[]: 123456

# Returns
[
  {"id": 1, "username": "user1", ...},
  {"id": 2, "username": "user2", ...},
  {"id": 123456, "username": "user3", ...}
]
```

### Get User Social Links
```python
# Python Method
socials = await user.get_socials()

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/{user_id}/social/buttons

# Returns
[
  {"url": "https://twitter.com/...", "type": "twitter"},
  {"url": "https://instagram.com/...", "type": "instagram"}
]
```

### Block/Unblock User
```python
# Python Method
await user.block()    # Block user
await user.unblock()  # Unblock user

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/users/{user_id}/block    # Block
DELETE https://onlyfans.com/api2/v2/users/{user_id}/block  # Unblock

# Returns
{"success": true}
```

---

## 3. Content Fetching Endpoints

### Get User Posts
```python
# Python Method
posts = await user.get_posts(
    limit=50,           # Default: 50
    offset=0,           # For pagination
    label="",           # "" | "archived" | "private_archived"
    after_date=None     # Filter by date
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/{user_id}/posts
    ?limit={limit}
    &offset={offset}
    &order=publish_date_desc
    &skip_users_dups=0
    &label={label}
    &afterPublishTime={timestamp}

# Returns
{
  "list": [
    {
      "id": 123456789,
      "text": "Post text",
      "price": 0,
      "isOpened": true,
      "isArchived": false,
      "createdAt": "2025-01-01T00:00:00+00:00",
      "media": [...],
      "author": {...},
      "favoritesCount": 100,
      "commentsCount": 50
    }
  ],
  "hasMore": true
}

# Usage Example
# Get all posts
all_posts = []
offset = 0
while True:
    posts = await user.get_posts(limit=100, offset=offset)
    if not posts:
        break
    all_posts.extend(posts)
    offset += 100
```

### Get Specific Post
```python
# Python Method
post = await user.get_post(post_id=123456789)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/posts/{post_id}

# Returns
{
  "id": 123456789,
  "text": "Post content",
  "price": 999,  # in cents
  "media": [...],
  "author": {...}
}
```

### Get User Stories
```python
# Python Method
stories = await user.get_stories(limit=100, offset=0)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/users/{user_id}/stories
    ?limit={limit}
    &offset={offset}

# Returns
{
  "list": [
    {
      "id": 987654321,
      "userId": 123456,
      "createdAt": "2025-01-01T00:00:00+00:00",
      "media": [...]
    }
  ],
  "hasMore": false
}
```

### Get Archived Stories
```python
# Python Method
archived = await user.get_archived_stories(limit=100, offset=0)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/stories/archive/
    ?limit={limit}
    &marker={offset}
    &order=publish_date_desc

# Note: Uses marker-based pagination
```

### Get Story Highlights
```python
# Python Method
# Get all highlights
highlights = await user.get_highlights()

# Get specific highlight
highlight_stories = await user.get_highlights(highlight_id=123)

# OnlyFans API Endpoints
# List highlights
GET https://onlyfans.com/api2/v2/users/{user_id}/stories/highlights
    ?limit=100&offset=0&order=desc

# Get highlight stories
GET https://onlyfans.com/api2/v2/stories/highlights/{highlight_id}
```

---

## 4. Messaging Endpoints

### Get Messages with User
```python
# Python Method
messages = await user.get_messages(
    limit=20,         # Default: 20
    offset_id=None,   # Message ID for pagination
    cutoff_id=None    # Stop at this message ID
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/chats/{user_id}/messages
    ?limit={limit}
    &id={offset_id}
    &order=desc

# Returns
{
  "list": [
    {
      "id": 111222333,
      "text": "Message text",
      "price": 0,
      "isOpened": true,
      "isFree": true,
      "isPurchased": true,
      "isMediaReady": true,
      "media": [...],
      "createdAt": "2025-01-01T00:00:00+00:00",
      "fromUser": {...}
    }
  ],
  "hasMore": true
}

# Usage Example - Get all messages
all_messages = []
offset_id = None
while True:
    messages = await user.get_messages(limit=100, offset_id=offset_id)
    if not messages:
        break
    all_messages.extend(messages)
    offset_id = messages[-1].id
```

### Send Message
```python
# Python Method
message = await user.send_message(
    text="Hello!",
    price=0,              # 0 for free, amount in cents for PPV
    media_ids=[],         # List of media IDs to attach
    locked_text=False     # Lock text until paid
)

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/chats/{user_id}/messages

# Request Body
{
  "text": "Hello!",
  "lockedText": false,
  "mediaFiles": [],
  "price": 0,
  "isCouplePeopleMedia": false,
  "isForward": false
}

# Returns
{
  "id": 999888777,
  "text": "Hello!",
  "price": 0,
  "createdAt": "2025-01-01T00:00:00+00:00"
}

# Usage Examples
# Send free message
await user.send_message("Thanks for subscribing!")

# Send PPV message ($10)
await user.send_message("Exclusive content!", price=1000)

# Send with media
await user.send_message("Check this out!", media_ids=[123, 456])
```

### Reply to Message
```python
# Python Method
reply = await message.reply(
    text="Thanks!",
    price=0,
    media_ids=None,
    locked_text=False
)

# Uses same endpoint as send_message
# Automatically determines correct recipient
```

### Search Messages
```python
# Python Method
results = await user.search_messages(text="keyword")

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/chats/{user_id}/messages/search
    ?query={text}

# Alternative endpoint
GET https://onlyfans.com/api2/v2/chats/{user_id}
    ?limit=10&offset=0&filter=&order=activity&query={text}
```

---

## 5. Subscription Endpoints

### Get Active Subscriptions
```python
# Python Method
subscriptions = await authed.get_subscriptions(
    sub_type="active",    # "all" | "active" | "expired"
    limit=100,
    offset=0,
    filter_by=None
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/subscriptions/subscribes
    ?limit={limit}
    &offset={offset}
    &type={sub_type}
    &filter[{filter}]=1
    &format=infinite

# Returns
{
  "list": [
    {
      "id": 123,
      "userId": 456789,
      "subscribedBy": 123456,
      "expiredAt": "2025-02-01T00:00:00+00:00",
      "price": 999,
      "regularPrice": 999,
      "discount": 0,
      "user": {...}  # Full user object
    }
  ],
  "hasMore": true
}

# Usage Example
# Get all active subscriptions
active = await authed.get_subscriptions(sub_type="active")
for sub in active:
    print(f"Subscribed to {sub.user.username} until {sub.expired_at}")
```

### Get Subscription Count
```python
# Internal method used by get_subscriptions()

# OnlyFans API Endpoints
GET https://onlyfans.com/api2/v2/subscriptions/count/{sub_type}
# or
GET https://onlyfans.com/api2/v2/subscriptions/subscribes/count
    ?type={sub_type}&filter[{filter}]=1

# Returns
{"count": 150}
```

### Subscribe to User
```python
# Python Method
result = await user.buy_subscription()

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/payments/pay

# Request Body
{
  "paymentType": "subscribe",
  "userId": 123456,
  "subscribeSource": "profile",
  "amount": 999,  # in cents
  "token": "",
  "unavailablePaymentGates": []
}

# Returns
{
  "success": true,
  "subscribedData": {...}
}
```

---

## 6. Chat and Communication Endpoints

### Get All Chats
```python
# Python Method
chats = await authed.get_chats(limit=20, offset=0)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/chats
    ?limit={limit}
    &offset={offset}
    &order=recent

# Returns
{
  "list": [
    {
      "withUser": {...},   # User object
      "lastMessage": {...}, # Last message
      "unreadMessagesCount": 5,
      "canChat": true
    }
  ],
  "hasMore": true
}
```

### Get Mass Message Statistics
```python
# Python Method
stats = await authed.get_mass_message_stats(
    resume=False,
    limit=10,
    offset=0
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/messages/queue/stats
    ?limit={limit}
    &offset={offset}
    &format=infinite

# Returns
{
  "list": [
    {
      "id": 123,
      "queueId": 456,
      "status": "completed",
      "sentCount": 100,
      "failedCount": 0,
      "createdAt": "2025-01-01T00:00:00+00:00"
    }
  ],
  "hasMore": false
}
```

---

## 7. Payment and Transaction Endpoints

### Get Paid Content
```python
# Python Method
paid_content = await authed.get_paid_content(
    performer_id=None,  # Filter by specific user
    limit=10,
    offset=0
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/posts/paid
    ?limit={limit}
    &offset={offset}
    &format=infinite
    &user_id={performer_id}  # Optional

# Returns
{
  "list": [
    {
      "responseType": "post",  # or "message"
      "id": 123456,
      "price": 1999,
      "text": "PPV content",
      "media": [...],
      "author": {...}
    }
  ],
  "hasMore": true
}
```

### Buy PPV Message
```python
# Python Method
result = await message.buy_message()

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/payments/pay

# Request Body
{
  "amount": 500,        # Price in cents
  "messageId": 123456,
  "paymentType": "message",
  "token": "",
  "unavailablePaymentGates": []
}

# Returns
{
  "success": true,
  "result": {...}
}
```

### Buy PPV Post
```python
# Python Method
result = await post.buy_ppv()

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/payments/pay

# Request Body
{
  "paymentType": "post",
  "postId": 123456,
  "amount": 999,
  "userId": 789,  # Post author ID
  "token": "",
  "unavailablePaymentGates": []
}
```

### Get Transactions
```python
# Python Method
transactions = await authed.get_transactions()

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/payments/all/transactions
    ?limit=10&offset=0

# Returns transaction history
```

---

## 8. List Management Endpoints

### Get User Lists
```python
# Python Method
lists = await authed.get_lists(limit=100, offset=0)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/lists
    ?limit={limit}
    &offset={offset}

# Returns
{
  "list": [
    {
      "id": 123,
      "name": "Favorites",
      "usersCount": 50,
      "createdAt": "2025-01-01T00:00:00+00:00"
    }
  ],
  "hasMore": false
}
```

### Get Users in List
```python
# Python Method
users = await authed.get_lists_users(
    identifier=123,  # List ID
    limit=50,
    offset=0
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/lists/{list_id}/users
    ?limit={limit}
    &offset={offset}
    &query=

# Returns list of user objects
```

---

## 9. Vault Management Endpoints

### Get Vault Lists
```python
# Python Method
vault_lists = await authed.get_vault_lists(limit=50, offset=0)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/vault/lists
    ?view=main
    &limit={limit}
    &offset={offset}
    &order=media_count_desc

# Returns vault collections
```

### Get Vault Media
```python
# Python Method
vault_media = await authed.get_vault_media(
    list_id=123,
    limit=50,
    offset=0
)

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/vault/media
    ?limit={limit}
    &offset={offset}
    &order=created_at_desc
    &field=recent
    &list={list_id}

# Returns media items in vault
```

---

## 10. Interaction Endpoints

### Like/Unlike Content
```python
# Python Method
# Like
await user.like(category="posts", identifier=123456)
# Unlike
await user.unlike(category="posts", identifier=123456)

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/{category}/{content_id}/like    # Like
DELETE https://onlyfans.com/api2/v2/{category}/{content_id}/like  # Unlike

# Categories: "posts", "messages"
# Returns
{"success": true}
```

### Get Post Comments
```python
# Python Method
comments = await post.get_comments()

# OnlyFans API Endpoint
GET https://onlyfans.com/api2/v2/posts/{post_id}/comments
    ?limit=30
    &offset=0
    &sort=desc  # or "asc"

# Returns
{
  "list": [
    {
      "id": 789,
      "text": "Great post!",
      "author": {...},
      "createdAt": "2025-01-01T00:00:00+00:00"
    }
  ],
  "hasMore": false
}
```

### Favorite/Unfavorite Post
```python
# Python Method
await post.favorite()

# OnlyFans API Endpoint
POST https://onlyfans.com/api2/v2/posts/{post_id}/favorites/{user_id}
```

---

## 11. DRM and Media Protection Endpoints

### Get DRM Signature
```python
# Python Method (internal)
signature = await drm.get_signature(media_item)

# OnlyFans API Endpoints
# For regular media
GET https://onlyfans.com/api2/v2/users/media/{media_id}/drm/?type=widevine

# For mass messages
GET https://onlyfans.com/api2/v2/users/media/{media_id}/drm/message/{message_id}?type=widevine

# Returns
{
  "signature": "base64_encoded_signature",
  "publicKey": "base64_encoded_key",
  "sessionId": "session_123"
}
```

---

## Key Usage Patterns

### 1. Authentication Headers
All requests require these headers:
```python
headers = {
    "Cookie": "auth_id=123; sess=abc; ...",
    "X-BC": "browser_check_token",
    "User-Agent": "Mozilla/5.0...",
    "app-token": "33d57ade8c02dbc5a333db99ff9ae26a",
    "sign": "41105:sha1_hash:checksum:681c9271",
    "time": "1754513736"
}
```

### 2. Dynamic Headers Calculation
```python
# Sign header format
sign = "{prefix}:{sha1_hash}:{checksum}:{suffix}"

# SHA1 calculation
message = "\n".join([
    static_param,  # From dynamic rules
    timestamp,
    url_path,
    auth_id
])
sha1_hash = sha1(message).hexdigest()

# Checksum
checksum = sum(sha1_bytes[i] for i in checksum_indexes) + checksum_constant
```

### 3. Pagination Patterns
```python
# Standard pagination
params = {
    "limit": 100,    # Max items per request
    "offset": 0      # Starting position
}

# ID-based pagination (messages)
params = {
    "limit": 100,
    "id": last_message_id  # Continue from this ID
}

# Marker-based pagination (archived stories)
params = {
    "limit": 100,
    "marker": last_marker
}
```

### 4. Error Handling
```python
try:
    result = await api_call()
except Exception as e:
    if "429" in str(e):
        # Rate limited - wait and retry
        await asyncio.sleep(60)
    elif "401" in str(e):
        # Auth expired - re-login
        await api.login(auth_json)
```

### 5. Rate Limiting
OnlyFans limits:
- ~1000 requests per 5 minutes
- Implement delays between requests
- Use batch operations when possible

### 6. Media URL Security
Media URLs are:
- IP-locked to requester
- Time-limited (expire after set period)
- Signed with AWS CloudFront signatures
- Must be downloaded immediately

---

## Complete Usage Example

```python
import asyncio
from ultima_scraper_api import OnlyFansAPI

async def complete_example():
    # Initialize
    api = OnlyFansAPI()
    
    # Authenticate
    auth_json = {
        "auth": {
            "id": 123456,
            "cookie": "full_cookie_string",
            "x_bc": "token",
            "user_agent": "Mozilla/5.0..."
        }
    }
    authed = await api.login(auth_json)
    
    # Get user
    user = await authed.get_user("modelname")
    
    # Fetch all content types
    posts = await user.get_posts(limit=100)
    messages = await user.get_messages(limit=50)
    stories = await user.get_stories()
    
    # Send message
    msg = await user.send_message("Hello!")
    
    # Get subscriptions
    subs = await authed.get_subscriptions(sub_type="active")
    
    # Process posts
    for post in posts:
        if post.price > 0:
            print(f"PPV Post: ${post.price/100}")
        
        # Get comments
        comments = await post.get_comments()
        
        # Like post
        await user.like("posts", post.id)
    
    # Cleanup
    await api.close_pools()

# Run
asyncio.run(complete_example())
```

This comprehensive mapping covers all major API endpoints used by UltimaScraperAPI to interact with OnlyFans.