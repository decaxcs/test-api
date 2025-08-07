# Python Guide for UltimaScraperAPI Flask Wrapper

Complete Python examples for using the API with the `requests` library.

## Installation

```bash
pip install requests
```

## Basic Setup

```python
import requests
import json

# API base URL
BASE_URL = "http://localhost:5000/api"

# Optional: If you want to provide auth directly instead of using auth.json
AUTH_DATA = {
    "auth": {
        "id": "your_user_id",
        "cookie": "your_cookie_string", 
        "user_agent": "Mozilla/5.0...",
        "x_bc": "optional_token"
    }
}
```

## Authentication

### Method 1: Using auth.json file
```python
import requests

# Authenticate using auth.json file on server
response = requests.post(f"{BASE_URL}/auth")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Logged in as: {data['user']['username']}")
else:
    print(f"❌ Authentication failed: {response.json()}")
```

### Method 2: Providing auth data directly
```python
import requests

# Authenticate with provided credentials
auth_payload = {
    "auth": {
        "id": "123456",
        "cookie": "auth_id=xxx; sess=yyy;",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "x_bc": "optional_token"
    }
}

response = requests.post(f"{BASE_URL}/auth", json=auth_payload)

if response.status_code == 200:
    print("✅ Authentication successful!")
    print(response.json())
else:
    print(f"❌ Failed: {response.json()['error']}")
```

## Get Current User Info

```python
# Get info about the authenticated user
response = requests.get(f"{BASE_URL}/me")

if response.status_code == 200:
    user = response.json()
    print(f"Username: {user['username']}")
    print(f"Name: {user['name']}")
    print(f"Posts: {user['posts_count']}")
    print(f"Verified: {user['is_verified']}")
else:
    print(f"Error: {response.json()['error']}")
```

## Get User Profile

```python
# Get a specific user's profile
username = "someusername"
response = requests.get(f"{BASE_URL}/user/{username}")

if response.status_code == 200:
    user = response.json()
    print(f"User ID: {user['id']}")
    print(f"Username: {user['username']}")
    print(f"Bio: {user['bio']}")
    print(f"Posts: {user['posts_count']}")
    print(f"Photos: {user['photos_count']}")
    print(f"Videos: {user['videos_count']}")
elif response.status_code == 404:
    print("User not found")
else:
    print(f"Error: {response.json()['error']}")
```

## Get User Posts

```python
# Get posts from a user with pagination
username = "someusername"
limit = 20
offset = 0

response = requests.get(
    f"{BASE_URL}/user/{username}/posts",
    params={"limit": limit, "offset": offset}
)

if response.status_code == 200:
    data = response.json()
    posts = data['posts']
    
    print(f"Found {data['count']} posts")
    
    for post in posts:
        print(f"\n--- Post {post['id']} ---")
        print(f"Text: {post['text']}")
        print(f"Price: ${post['price']}")
        print(f"Created: {post['created_at']}")
        print(f"Likes: {post['likes_count']}")
        
        # Print media if available
        if post['media']:
            print(f"Media: {len(post['media'])} items")
            for media in post['media']:
                print(f"  - {media['type']}: {media['url']}")
```

## Get Messages

```python
# Get messages with a specific user
username = "someusername"

response = requests.get(
    f"{BASE_URL}/user/{username}/messages",
    params={"limit": 50}
)

if response.status_code == 200:
    data = response.json()
    messages = data['messages']
    
    print(f"Found {len(messages)} messages")
    
    for msg in messages:
        sender = "User" if msg['is_from_user'] else "You"
        print(f"\n[{sender}] {msg['created_at']}")
        print(f"Message: {msg['text']}")
        
        if msg['price'] > 0:
            print(f"Price: ${msg['price']}")
        
        if msg['media']:
            print(f"Attachments: {len(msg['media'])}")
```

## Get Stories

```python
# Get stories from a user
username = "someusername"

response = requests.get(f"{BASE_URL}/user/{username}/stories")

if response.status_code == 200:
    data = response.json()
    stories = data['stories']
    
    print(f"Found {data['count']} stories")
    
    for story in stories:
        print(f"\nStory {story['id']}")
        print(f"Created: {story['created_at']}")
        print(f"Expires: {story['expires_at']}")
        print(f"Viewed: {story['is_viewed']}")
        
        if story['media']:
            for media in story['media']:
                print(f"  - {media['type']}: {media['url']}")
```

## Get Subscriptions

```python
# Get your active subscriptions
response = requests.get(
    f"{BASE_URL}/subscriptions",
    params={"limit": 100}
)

if response.status_code == 200:
    data = response.json()
    subs = data['subscriptions']
    
    print(f"You have {len(subs)} subscriptions\n")
    
    for sub in subs:
        print(f"Username: {sub['username']}")
        print(f"Name: {sub['name']}")
        print(f"Price: ${sub['subscription']['price']}")
        print(f"Status: {sub['subscription']['status']}")
        print(f"Expires: {sub['subscription']['expires_at']}")
        print(f"Auto-renew: {sub['subscription']['renew']}")
        print("-" * 40)
```

## Complete Example Script

```python
import requests
import json
from datetime import datetime

class UltimaScraperClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def authenticate(self, auth_data=None):
        """Authenticate with the API"""
        url = f"{self.base_url}/auth"
        
        if auth_data:
            response = self.session.post(url, json=auth_data)
        else:
            response = self.session.post(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Auth failed: {response.json()}")
    
    def get_user(self, username):
        """Get user profile"""
        response = self.session.get(f"{self.base_url}/user/{username}")
        response.raise_for_status()
        return response.json()
    
    def get_posts(self, username, limit=50, offset=0):
        """Get user posts"""
        response = self.session.get(
            f"{self.base_url}/user/{username}/posts",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()
    
    def get_all_posts(self, username):
        """Get all posts from a user"""
        all_posts = []
        offset = 0
        limit = 50
        
        while True:
            data = self.get_posts(username, limit, offset)
            posts = data['posts']
            
            if not posts:
                break
                
            all_posts.extend(posts)
            offset += limit
            
            print(f"Fetched {len(all_posts)} posts so far...")
        
        return all_posts
    
    def download_media(self, post):
        """Download media from a post"""
        for media in post.get('media', []):
            if media['url']:
                # Download logic here
                print(f"Would download: {media['url']}")

# Usage example
if __name__ == "__main__":
    # Create client
    client = UltimaScraperClient()
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        auth_result = client.authenticate()
        print(f"✅ Logged in as: {auth_result['user']['username']}")
        
        # Get user info
        username = "targetusername"
        print(f"\n👤 Fetching user: {username}")
        user = client.get_user(username)
        print(f"Found: {user['name']} (@{user['username']})")
        print(f"Posts: {user['posts_count']}")
        
        # Get recent posts
        print(f"\n📝 Fetching recent posts...")
        posts_data = client.get_posts(username, limit=10)
        
        for post in posts_data['posts']:
            print(f"\nPost: {post['text'][:100]}...")
            print(f"Likes: {post['likes_count']}")
            print(f"Media: {len(post['media'])} items")
        
    except Exception as e:
        print(f"❌ Error: {e}")
```

## Error Handling

```python
import requests

def safe_api_call(url, method="GET", **kwargs):
    """Make API call with proper error handling"""
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        
        # Check for HTTP errors
        if response.status_code == 401:
            print("❌ Not authenticated. Please login first.")
            return None
        elif response.status_code == 404:
            print("❌ Resource not found.")
            return None
        elif response.status_code >= 500:
            print("❌ Server error. Try again later.")
            return None
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError:
        print("❌ Invalid response format.")
    
    return None

# Example usage
data = safe_api_call(f"{BASE_URL}/user/someuser")
if data:
    print(f"User: {data['username']}")
```

## Tips

1. **Session Management**: Use `requests.Session()` to maintain cookies between requests
2. **Rate Limiting**: Add delays between requests to avoid overwhelming the server
3. **Error Handling**: Always check status codes and handle errors gracefully
4. **Pagination**: Use limit/offset parameters to handle large datasets
5. **Async Operations**: For better performance with multiple requests, consider using `aiohttp`

## Async Example (Advanced)

```python
import aiohttp
import asyncio

async def fetch_user_async(session, username):
    async with session.get(f"{BASE_URL}/user/{username}") as response:
        return await response.json()

async def fetch_multiple_users(usernames):
    async with aiohttp.ClientSession() as session:
        # First authenticate
        async with session.post(f"{BASE_URL}/auth") as response:
            if response.status != 200:
                print("Auth failed")
                return
        
        # Fetch all users concurrently
        tasks = [fetch_user_async(session, username) for username in usernames]
        results = await asyncio.gather(*tasks)
        
        return results

# Usage
usernames = ["user1", "user2", "user3"]
users = asyncio.run(fetch_multiple_users(usernames))
```