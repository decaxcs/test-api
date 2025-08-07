# UltimaScraperAPI - Ultimate Cheat Sheet 🚀

A complete guide to using UltimaScraperAPI for OnlyFans and Fansly content scraping.

## Table of Contents
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Authentication Setup](#authentication-setup)
- [Python Examples](#python-examples)
- [JavaScript/Node.js Examples](#javascriptnodejs-examples)
- [API Reference](#api-reference)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Media Handling](#media-handling)
- [Advanced Features](#advanced-features)

---

## Quick Start

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/UltimaScraperAPI.git
cd UltimaScraperAPI

# Install dependencies
pip install -r requirements.txt

# Create auth.json (see Authentication Setup)
# Run your first script!
```

### Minimal Working Example (Python)
```python
import asyncio
from ultima_scraper_api import OnlyFansAPI

async def main():
    # Initialize API
    api = OnlyFansAPI()
    
    # Login with auth.json
    auth = {
        "auth": {
            "id": 123456789,
            "cookie": "full_cookie_string_here",
            "x_bc": "your_x_bc_value",
            "user_agent": "Mozilla/5.0..."
        }
    }
    authed = await api.login(auth)
    
    # Get a user
    user = await authed.get_user("username")
    
    # Fetch content
    posts = await user.get_posts()
    print(f"Found {len(posts)} posts")
    
    # Cleanup
    await api.close_pools()

asyncio.run(main())
```

---

## Installation

### Python (Primary)
```bash
# Using pip
pip install ultima-scraper-api

# From source
git clone https://github.com/yourusername/UltimaScraperAPI.git
cd UltimaScraperAPI
pip install -r requirements.txt
```

### Node.js (Using API Server)
```bash
# Start the API server
python api_server.py

# Install axios for requests
npm install axios
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

---

## Authentication Setup

### Getting Your Cookies (Required)

1. **Login to OnlyFans/Fansly in your browser**
2. **Open Developer Tools** (F12)
3. **Go to Network tab** → Find any API request → Copy the cookie header
4. **Or go to Application → Cookies** → Select all cookies → Copy

### Creating auth.json (Current Format)
```json
{
  "auth": {
    "id": 513665682,
    "cookie": "fp=xxx; lang=en; csrf=xxx; cookiesAccepted=all; st=xxx; auth_id=513665682; sess=xxx; ref_src=xxx",
    "x_bc": "cf3b1fb800279c23f5429e36d741a127e1e134cb",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
  }
}
```

**Important:** 
- `id` is your numeric user ID (same as auth_id in cookies)
- `cookie` is the ENTIRE cookie string from your browser (copy all cookies as one string)
- `x_bc` is from the x-bc header in network requests (check Network tab)
- `user_agent` must match your browser's user agent exactly

**Note:** The old format with separate `auth_id`, `auth_uniq_`, etc. is deprecated. Use the new format with the complete cookie string.

### Complete Working Example
```json
{
  "auth": {
    "id": 513665682,
    "cookie": "fp=cf3b1fb800279c23f5429e36d741a127e1e134cb; lang=en; csrf=ve2xbOhF8131799226a30e70f7f77f3811e4e08f; cookiesAccepted=all; st=2a138abc2936f63eea77852ed17b9f4447ab7dd2fa374137c79c2d25bd08df24; auth_id=513665682; sess=mklrl4jc9e5vropanedq16fcdl; ref_src=",
    "x_bc": "cf3b1fb800279c23f5429e36d741a127e1e134cb",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
  }
}
```

### Security Best Practices
- **NEVER** commit auth.json to git
- Add `auth.json` to .gitignore
- Use environment variables in production
- Rotate cookies regularly

---

## Python Examples

### Basic Usage

```python
import asyncio
import json
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

async def basic_example():
    # Load config
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    # Load auth from file
    with open('auth.json', 'r') as f:
        auth_data = json.load(f)
    
    # Login - pass the entire auth_data object
    authed = await api.login(auth_data)
    if not authed:
        print("Login failed!")
        return
    
    # Get user by username
    user = await authed.get_user("example_username")
    
    # Get all posts
    posts = await user.get_posts(limit=10)
    for post in posts:
        print(f"Post: {post.text[:50]}...")
        print(f"Likes: {post.likes_count}")
        print(f"Price: ${post.price/100 if post.price else 0}")
    
    await api.close_pools()

asyncio.run(basic_example())
```

### Fetching All Content Types

```python
async def fetch_all_content(username: str):
    api = OnlyFansAPI()
    authed = await api.login(auth_json)
    user = await authed.get_user(username)
    
    # Posts
    posts = await user.get_posts()
    print(f"Posts: {len(posts)}")
    
    # Messages
    messages = await user.get_messages()
    print(f"Messages: {len(messages)}")
    
    # Stories
    stories = await user.get_stories()
    print(f"Stories: {len(stories)}")
    
    # Highlights
    highlights = await user.get_highlights()
    print(f"Highlights: {len(highlights)}")
    
    # Archived Stories
    archived = await user.get_archived_stories()
    print(f"Archived: {len(archived)}")
    
    # Paid Content
    paid = await user.get_paid_contents()
    print(f"Paid content: {len(paid)}")
    
    await api.close_pools()
```

### Downloading Media

```python
import aiohttp
import aiofiles
from pathlib import Path

async def download_media(user, post):
    """Download all media from a post"""
    download_dir = Path(f"downloads/{user.username}")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    for media in post.media:
        if media.get('canView'):
            # Get media URL
            url_obj = post.url_picker(media)
            if not url_obj:
                continue
                
            url = url_obj.geturl()
            
            # Determine filename
            media_id = media.get('id', 'unknown')
            media_type = media.get('type', 'unknown')
            ext = '.jpg' if media_type == 'photo' else '.mp4'
            filename = download_dir / f"{post.id}_{media_id}{ext}"
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(filename, 'wb') as f:
                            await f.write(await resp.read())
                        print(f"Downloaded: {filename}")
```

### Sending Messages

```python
async def messaging_examples(username: str):
    api = OnlyFansAPI()
    authed = await api.login(auth_json)
    user = await authed.get_user(username)
    
    # Send free message
    msg1 = await user.send_message("Hello! How are you?")
    
    # Send paid message ($10)
    msg2 = await user.send_message(
        "Exclusive content just for you!",
        price=1000  # in cents
    )
    
    # Send message with media
    msg3 = await user.send_message(
        "Check out these photos!",
        media_ids=[12345, 67890]
    )
    
    # Reply to a message
    messages = await user.get_messages(limit=1)
    if messages:
        reply = await messages[0].reply("Thanks for your message!")
    
    await api.close_pools()
```

### Pagination and Bulk Fetching

```python
async def fetch_all_posts_paginated(user):
    """Fetch ALL posts using pagination"""
    all_posts = []
    offset = 0
    limit = 100  # Max per request
    
    while True:
        posts = await user.get_posts(limit=limit, offset=offset)
        if not posts:
            break
            
        all_posts.extend(posts)
        print(f"Fetched {len(posts)} posts (total: {len(all_posts)})")
        
        offset += limit
        await asyncio.sleep(1)  # Rate limiting
    
    return all_posts
```

### Handling Subscriptions

```python
async def subscription_management():
    api = OnlyFansAPI()
    authed = await api.login(auth_json)
    
    # Get all subscriptions
    subs = await authed.get_subscriptions()
    print(f"Active subscriptions: {len(subs)}")
    
    # Get expired subscriptions
    expired = await authed.get_expired_subscriptions()
    print(f"Expired subscriptions: {len(expired)}")
    
    # Subscribe to a user
    user = await authed.get_user("username")
    result = await user.subscribe()
    
    # Unsubscribe
    result = await user.unsubscribe()
    
    await api.close_pools()
```

---

## JavaScript/Node.js Examples

### Using the API Server

First, start the API server:
```bash
python api_server.py
```

### Basic Request (Node.js)

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:5000';
const AUTH_DATA = {
    id: 513665682,
    cookie: "fp=xxx; lang=en; csrf=xxx; cookiesAccepted=all; st=xxx; auth_id=513665682; sess=xxx",
    x_bc: "cf3b1fb800279c23f5429e36d741a127e1e134cb",
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
};

async function loginAndFetchUser() {
    try {
        // Login
        const loginResp = await axios.post(`${API_BASE}/login`, {
            site: 'onlyfans',
            auth: AUTH_DATA
        });
        
        const sessionId = loginResp.data.session_id;
        console.log('Logged in:', sessionId);
        
        // Get user
        const userResp = await axios.get(`${API_BASE}/user/example_username`, {
            headers: { 'X-Session-ID': sessionId }
        });
        
        console.log('User:', userResp.data);
        
        // Get posts
        const postsResp = await axios.get(`${API_BASE}/user/example_username/posts?limit=10`, {
            headers: { 'X-Session-ID': sessionId }
        });
        
        console.log('Posts:', postsResp.data.length);
        
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

loginAndFetchUser();
```

### Fetching Messages (JavaScript)

```javascript
async function fetchMessages(sessionId, username) {
    const response = await axios.get(
        `${API_BASE}/user/${username}/messages?limit=50`,
        { headers: { 'X-Session-ID': sessionId } }
    );
    
    const messages = response.data;
    
    // Process messages
    messages.forEach(msg => {
        console.log(`From: ${msg.fromUser.username}`);
        console.log(`Text: ${msg.text}`);
        console.log(`Price: $${msg.price / 100}`);
        console.log(`Media: ${msg.mediaCount || 0} items`);
        console.log('---');
    });
    
    return messages;
}
```

### Sending Messages (JavaScript)

```javascript
async function sendMessage(sessionId, username, text, price = 0) {
    const response = await axios.post(
        `${API_BASE}/user/${username}/message`,
        {
            text: text,
            price: price,  // in cents
            mediaFiles: []
        },
        { headers: { 'X-Session-ID': sessionId } }
    );
    
    console.log('Message sent:', response.data);
    return response.data;
}

// Usage
await sendMessage(sessionId, 'username', 'Hello!');
await sendMessage(sessionId, 'username', 'PPV Content', 1000); // $10
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function OnlyFansUserProfile({ username }) {
    const [user, setUser] = useState(null);
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        async function fetchData() {
            try {
                // Assume sessionId is stored somewhere
                const sessionId = localStorage.getItem('of_session');
                
                // Fetch user
                const userResp = await axios.get(
                    `/api/user/${username}`,
                    { headers: { 'X-Session-ID': sessionId } }
                );
                setUser(userResp.data);
                
                // Fetch posts
                const postsResp = await axios.get(
                    `/api/user/${username}/posts?limit=20`,
                    { headers: { 'X-Session-ID': sessionId } }
                );
                setPosts(postsResp.data);
                
            } catch (error) {
                console.error('Error:', error);
            } finally {
                setLoading(false);
            }
        }
        
        fetchData();
    }, [username]);
    
    if (loading) return <div>Loading...</div>;
    
    return (
        <div>
            <h1>{user?.name || username}</h1>
            <p>Posts: {user?.postsCount}</p>
            <p>Photos: {user?.photosCount}</p>
            <p>Videos: {user?.videosCount}</p>
            
            <div className="posts">
                {posts.map(post => (
                    <div key={post.id} className="post">
                        <p>{post.text}</p>
                        <p>Likes: {post.favoritesCount}</p>
                        {post.price > 0 && <p>Price: ${post.price / 100}</p>}
                    </div>
                ))}
            </div>
        </div>
    );
}
```

---

## API Reference

### Core Classes

#### OnlyFansAPI
```python
api = OnlyFansAPI(config)
await api.login(auth_json)
await api.close_pools()
```

#### AuthModel (Authenticated Session)
```python
# User management
user = await authed.get_user(username)
users = await authed.get_users([username1, username2])

# Subscriptions
subs = await authed.get_subscriptions()
expired = await authed.get_expired_subscriptions()

# Content
lists = await authed.get_lists()
paid_content = await authed.get_paid_content()
```

#### UserModel
```python
# Content fetching
posts = await user.get_posts(limit=100, offset=0)
messages = await user.get_messages(limit=100, offset_id=None)
stories = await user.get_stories()
highlights = await user.get_highlights()
archived = await user.get_archived_stories()

# Specific content
post = await user.get_post(post_id)
message = await user.get_message_by_id(message_id)

# Actions
await user.subscribe()
await user.unsubscribe()
await user.favorite()
await user.send_message(text, price=0)
```

#### MessageModel
```python
# Purchase PPV
await message.buy_message()

# Reply
await message.reply(text, price=0)

# Get media URLs
url = message.url_picker(media_item)
```

#### PostModel
```python
# Actions
await post.like()
await post.unlike()
await post.buy_post()

# Get data
comments = await post.get_comments()
```

---

## Common Patterns

### Error Handling

```python
async def safe_api_call():
    try:
        api = OnlyFansAPI()
        authed = await api.login(auth_json)
        
        if not authed or not authed.is_authed():
            raise Exception("Authentication failed")
            
        user = await authed.get_user("username")
        if not user:
            raise Exception("User not found")
            
        posts = await user.get_posts()
        return posts
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return []
        
    finally:
        if 'api' in locals():
            await api.close_pools()
```

### Retry Logic

```python
import asyncio
from typing import Optional, Callable, Any

async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> Optional[Any]:
    """Retry an async function with exponential backoff"""
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            wait_time = delay * (backoff ** attempt)
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    return None

# Usage
posts = await retry_async(lambda: user.get_posts(limit=100))
```

### Concurrent Operations

```python
async def fetch_multiple_users_concurrently(usernames: list):
    """Fetch multiple users concurrently"""
    api = OnlyFansAPI()
    authed = await api.login(auth_json)
    
    # Create tasks
    tasks = [authed.get_user(username) for username in usernames]
    
    # Run concurrently
    users = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out errors
    valid_users = [u for u in users if not isinstance(u, Exception)]
    
    await api.close_pools()
    return valid_users
```

### Caching Results

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPI:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    async def get_user_cached(self, username: str):
        # Check cache
        if username in self.cache:
            cached_data, timestamp = self.cache[username]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        # Fetch fresh data
        api = OnlyFansAPI()
        authed = await api.login(auth_json)
        user = await authed.get_user(username)
        
        # Update cache
        self.cache[username] = (user, datetime.now())
        
        await api.close_pools()
        return user
```

---

## Rate Limiting

### Built-in Rate Limiter
```python
# The API has built-in rate limiting
# You can configure it in the session manager

from ultima_scraper_api.managers.session_manager import SessionManager

# Custom rate limit
session = SessionManager(
    max_rate=10,  # requests per second
    burst_size=20  # burst capacity
)
```

### Manual Rate Limiting
```python
import asyncio
from typing import List

class RateLimiter:
    def __init__(self, rate: int = 10):
        self.rate = rate
        self.tokens = rate
        self.updated_at = asyncio.get_event_loop().time()
    
    async def acquire(self):
        while self.tokens <= 0:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.updated_at
            self.tokens += elapsed * self.rate
            self.tokens = min(self.tokens, self.rate)
            self.updated_at = now
            
            if self.tokens <= 0:
                await asyncio.sleep(1 / self.rate)
        
        self.tokens -= 1

# Usage
limiter = RateLimiter(rate=5)  # 5 requests per second

async def fetch_with_limit(user):
    await limiter.acquire()
    return await user.get_posts()
```

---

## Media Handling

### Understanding Media Status

```python
def analyze_media(message):
    """Analyze media accessibility"""
    if not message.media:
        return "No media"
    
    for media in message.media:
        can_view = media.get('canView')
        media_type = media.get('type')
        
        if can_view is None:
            status = "Not loaded (probably PPV)"
        elif can_view is False:
            status = "Locked (needs purchase)"
        else:
            status = "Accessible"
        
        print(f"Media: {media_type} - Status: {status}")
        
        if can_view:
            # Try to get URL
            url_obj = message.url_picker(media)
            if url_obj:
                print(f"URL: {url_obj.geturl()}")
```

### Batch Media Download

```python
import aiohttp
import asyncio
from pathlib import Path

class MediaDownloader:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads
    
    async def download_file(self, url: str, filepath: Path):
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        return True
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                return False
    
    async def download_post_media(self, post, base_dir: Path):
        """Download all media from a post"""
        tasks = []
        
        for i, media in enumerate(post.media):
            if not media.get('canView'):
                continue
            
            url_obj = post.url_picker(media)
            if not url_obj:
                continue
            
            url = url_obj.geturl()
            ext = '.jpg' if media.get('type') == 'photo' else '.mp4'
            filepath = base_dir / f"{post.id}_{i}{ext}"
            
            tasks.append(self.download_file(url, filepath))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            success = sum(results)
            print(f"Downloaded {success}/{len(tasks)} files for post {post.id}")

# Usage
async def download_all_media(user):
    base_dir = Path(f"downloads/{user.username}")
    
    async with aiohttp.ClientSession() as session:
        downloader = MediaDownloader(session)
        
        posts = await user.get_posts(limit=50)
        for post in posts:
            await downloader.download_post_media(post, base_dir)
```

---

## Advanced Features

### Custom Session Configuration

```python
from ultima_scraper_api.config import UltimaScraperAPIConfig

# Custom configuration
config = UltimaScraperAPIConfig()
config.session_manager.proxies = ["http://proxy1.com", "http://proxy2.com"]
config.session_manager.max_threads = 10
config.session_manager.timeout = 30

api = OnlyFansAPI(config)
```

### Webhook Integration

```python
import aiohttp

async def notify_webhook(event: str, data: dict):
    """Send notifications to webhook"""
    webhook_url = "https://your-webhook.com/endpoint"
    
    payload = {
        "event": event,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)

# Usage in scraping
async def scrape_with_notifications(username):
    user = await authed.get_user(username)
    posts = await user.get_posts()
    
    # Notify webhook
    await notify_webhook("posts_scraped", {
        "username": username,
        "post_count": len(posts),
        "latest_post_id": posts[0].id if posts else None
    })
```

### Database Integration

```python
import asyncpg
from datetime import datetime

class DatabaseStorage:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.db_url)
    
    async def store_post(self, post, user):
        """Store post in database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO posts (id, user_id, username, text, price, created_at, media_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE
                SET text = $4, price = $5, updated_at = NOW()
            """, post.id, user.id, user.username, post.text, 
                post.price or 0, post.created_at, len(post.media))
    
    async def store_media(self, media, post_id):
        """Store media information"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO media (id, post_id, type, can_view, url)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO NOTHING
            """, media.get('id'), post_id, media.get('type'), 
                media.get('canView'), media.get('url'))

# Usage
db = DatabaseStorage("postgresql://user:pass@localhost/dbname")
await db.connect()

posts = await user.get_posts()
for post in posts:
    await db.store_post(post, user)
    for media in post.media:
        await db.store_media(media, post.id)
```

### Export Functions

```python
import json
import csv
from datetime import datetime

def export_to_json(posts, filename: str):
    """Export posts to JSON"""
    data = []
    for post in posts:
        data.append({
            "id": post.id,
            "text": post.text,
            "price": post.price,
            "likes": post.likes_count,
            "created_at": post.created_at.isoformat(),
            "media_count": len(post.media),
            "media": [
                {
                    "id": m.get('id'),
                    "type": m.get('type'),
                    "can_view": m.get('canView')
                } for m in post.media
            ]
        })
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def export_to_csv(messages, filename: str):
    """Export messages to CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'From', 'Text', 'Price', 'Media Count', 'Created'])
        
        for msg in messages:
            writer.writerow([
                msg.id,
                msg.get_author().username,
                msg.text[:100],  # Truncate long text
                msg.price / 100 if msg.price else 0,
                msg.media_count or 0,
                msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
```

### Monitoring and Logging

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ScraperMonitor:
    def __init__(self):
        self.stats = {
            'users_scraped': 0,
            'posts_fetched': 0,
            'messages_fetched': 0,
            'media_downloaded': 0,
            'errors': 0
        }
        self.start_time = datetime.now()
    
    def log_activity(self, activity: str, count: int = 1):
        self.stats[activity] = self.stats.get(activity, 0) + count
        logger.info(f"{activity}: +{count} (total: {self.stats[activity]})")
    
    def get_report(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            **self.stats,
            'elapsed_seconds': elapsed,
            'posts_per_second': self.stats['posts_fetched'] / elapsed if elapsed > 0 else 0
        }

# Usage
monitor = ScraperMonitor()

posts = await user.get_posts()
monitor.log_activity('posts_fetched', len(posts))

print(monitor.get_report())
```

---

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check if cookies are expired
   - Verify all required fields in auth.json
   - Ensure user_agent matches your browser

2. **Rate Limiting**
   - Add delays between requests
   - Use built-in rate limiter
   - Implement retry logic

3. **Media URLs Not Working**
   - URLs are IP-locked and temporary
   - Download immediately after fetching
   - Check if content is PPV

4. **Connection Errors**
   - Check internet connection
   - Verify proxy settings
   - Increase timeout values

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logging.getLogger('ultima_scraper_api').setLevel(logging.DEBUG)
```

---

## Best Practices

1. **Always use context managers or cleanup**
   ```python
   async with api.login_context(auth_json) as authed:
       # Your code here
   # Automatic cleanup
   ```

2. **Handle pagination properly**
   ```python
   all_items = []
   offset = 0
   while True:
       items = await user.get_posts(limit=100, offset=offset)
       if not items:
           break
       all_items.extend(items)
       offset += 100
   ```

3. **Check authentication status**
   ```python
   if not authed or not authed.is_authed():
       raise Exception("Not authenticated")
   ```

4. **Use type hints**
   ```python
   from typing import List, Optional
   from ultima_scraper_api import PostModel
   
   async def process_posts(posts: List[PostModel]) -> Optional[dict]:
       # Your code here
   ```

5. **Implement proper error handling**
   ```python
   try:
       result = await risky_operation()
   except SpecificError as e:
       logger.error(f"Known error: {e}")
       # Handle gracefully
   except Exception as e:
       logger.exception("Unexpected error")
       raise
   ```

---

## Links and Resources

- **Repository**: [GitHub - UltimaScraperAPI](https://github.com/yourusername/UltimaScraperAPI)
- **Documentation**: [Full API Docs](https://ultimascraperapi.readthedocs.io)
- **Discord**: [Support Server](https://discord.gg/yourdiscord)
- **Issues**: [Bug Reports](https://github.com/yourusername/UltimaScraperAPI/issues)

---

## Legal Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with OnlyFans/Fansly terms of service and respecting content creators' rights. Do not use this tool to:
- Redistribute content without permission
- Violate platform terms of service
- Infringe on copyright or privacy rights

Always respect content creators and their work!

---

## Quick Reference Card

```python
# Initialize
api = OnlyFansAPI()

# Auth format
auth_json = {
    "auth": {
        "id": 513665682,
        "cookie": "full_cookie_string",
        "x_bc": "your_x_bc_value",
        "user_agent": "your_user_agent"
    }
}

authed = await api.login(auth_json)

# Get user
user = await authed.get_user("username")

# Fetch content
posts = await user.get_posts()
messages = await user.get_messages()
stories = await user.get_stories()

# Send message
await user.send_message("Hello!")

# Reply to message
await message.reply("Thanks!")

# Download media
url = post.url_picker(media_item).geturl()

# Cleanup
await api.close_pools()
```

---

*Last updated: 2025 | Version: 1.0*