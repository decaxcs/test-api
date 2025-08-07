# UltimaScraperAPI - API Functions Guide

## Main Entry Points

### 1. **ultima_scraper_api/__init__.py**
```python
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Initialize API
config = UltimaScraperAPIConfig()
api = OnlyFansAPI(config)

# Or use the factory function
from ultima_scraper_api import select_api
api = select_api("onlyfans", config)
```

### 2. **OnlyFansAPI (ultima_scraper_api/apis/onlyfans/onlyfans.py)**
Main API class with authentication methods:
```python
# Login method
authed = await api.login(auth_json)

# Login context manager
async with api.login_context(auth_json) as authed:
    # Use authed session here
```

### 3. **OnlyFansAuthModel (ultima_scraper_api/apis/onlyfans/classes/auth_model.py)**
After authentication, you get access to:
```python
# User management
user = await authed.get_user(username)  # Get a specific user
users = await authed.get_users(usernames_list)  # Get multiple users

# Subscriptions
subscriptions = await authed.get_subscriptions()
expired_subs = await authed.get_expired_subscriptions()

# Lists and collections
lists = await authed.get_lists()
vault_lists = await authed.get_vault_lists()

# Content
paid_content = await authed.get_paid_content()

# Chats
chats = await authed.get_chats()
```

### 4. **UserModel (ultima_scraper_api/apis/onlyfans/classes/user_model.py)**
Once you have a user object, you can call:
```python
# Content fetching
posts = await user.get_posts(limit=100, offset=0)
messages = await user.get_messages(limit=100, offset_id=None)
stories = await user.get_stories(limit=100)
highlights = await user.get_highlights()
archived_stories = await user.get_archived_stories()

# Specific content
post = await user.get_post(post_id, refresh=True)
message = await user.get_message_by_id(message_id)

# Media
avatar = await user.get_avatar()
header = await user.get_header()

# Other data
promotions = await user.get_promotions()
socials = await user.get_socials()
spotify = await user.get_spotify()
paid_contents = await user.get_paid_contents()

# Interaction
await user.subscribe()
await user.unsubscribe()
await user.favorite()
await user.unfavorite()

# Messaging
await user.send_message(text="Hello!", price=0, media_ids=None, locked_text=False)
# price=0 for free message, price=500 for $5.00 PPV message
```

### 5. **MessageModel (ultima_scraper_api/apis/onlyfans/classes/message_model.py)**
Message-specific functions:
```python
# Purchase PPV content
result = await message.buy_message()

# Refresh message data
refreshed = await message.refresh()

# Get media URLs
url = message.url_picker(media_item)
preview_url = message.preview_url_picker(media_item)

# Reply to message
reply = await message.reply(text="Thanks!", price=0, media_ids=None, locked_text=False)
# price=0 for free reply, price=500 for $5.00 PPV reply
```

### 6. **PostModel (ultima_scraper_api/apis/onlyfans/classes/post_model.py)**
Post-specific functions:
```python
# Purchase post
result = await post.buy_post()

# Get comments
comments = await post.get_comments()

# Like/unlike
await post.like()
await post.unlike()

# Archive/unarchive
await post.archive()
await post.unarchive()
```

## Example Usage Patterns

### Basic Authentication and User Fetching
```python
import asyncio
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

async def main():
    # Initialize
    api = OnlyFansAPI(UltimaScraperAPIConfig())
    
    # Authenticate
    auth_json = {"auth": {...}}  # From auth.json
    authed = await api.login(auth_json)
    
    # Get a user
    user = await authed.get_user("username")
    
    # Fetch content
    posts = await user.get_posts()
    messages = await user.get_messages()
    
    # Clean up
    await api.close_pools()

asyncio.run(main())
```

### Using Context Manager
```python
async def fetch_with_context():
    api = OnlyFansAPI()
    
    async with api.login_context(auth_json) as authed:
        if authed:
            user = await authed.get_user("username")
            posts = await user.get_posts()
            # Session automatically cleaned up
```

### Handling Media
```python
# For a message with media
for media_item in message.media:
    if media_item.get("canView"):
        url_result = message.url_picker(media_item)
        if url_result:
            cdn_url = url_result.geturl()
            # Download or process the media
```

### Messaging Examples
```python
# Send a free message
await user.send_message("Hello! How are you?")

# Send a paid PPV message ($10.00)
await user.send_message("Exclusive content!", price=1000)

# Send message with media
media_ids = [12345, 67890]  # Media IDs from uploaded content
await user.send_message("Check out these photos!", media_ids=media_ids)

# Send locked text PPV message
await user.send_message("Secret message", price=500, locked_text=True)

# Reply to a message
messages = await user.get_messages(limit=10)
if messages:
    latest_msg = messages[0]
    await latest_msg.reply("Thanks for your message!")

# Reply with PPV content
await latest_msg.reply("Here's the exclusive content you requested", price=2000, media_ids=[12345])
```

## Key Files for API Functions

1. **API Initialization**: `ultima_scraper_api/__init__.py`
2. **OnlyFans API**: `apis/onlyfans/onlyfans.py`
3. **Authentication**: `apis/onlyfans/authenticator.py`
4. **Auth Model**: `apis/onlyfans/classes/auth_model.py`
5. **User Model**: `apis/onlyfans/classes/user_model.py`
6. **Message Model**: `apis/onlyfans/classes/message_model.py`
7. **Post Model**: `apis/onlyfans/classes/post_model.py`
8. **Session Manager**: `managers/session_manager.py`

## Important Notes

- All API calls are **asynchronous** - use `await`
- Most content methods support pagination with `limit` and `offset`
- Media URLs are signed and IP-restricted
- PPV content requires purchase before media access
- Always call `api.close_pools()` or use context managers