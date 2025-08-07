# Postman Guide for UltimaScraperAPI Flask Wrapper

Complete guide for testing the API using Postman.

## Setup

1. **Download Postman**: https://www.postman.com/downloads/
2. **Start the API server**: 
   ```bash
   python api_server.py
   ```
3. **Create a new Collection** in Postman called "UltimaScraperAPI"

## Environment Setup

### 1. Create Environment Variables
1. Click the gear icon ⚙️ → "Manage Environments"
2. Add a new environment called "UltimaScraperAPI Local"
3. Add these variables:
   ```
   base_url: http://localhost:5000/api
   username: (leave empty, will fill later)
   ```

## API Endpoints

### 1. Health Check
**Test if the server is running**

- **Method**: `GET`
- **URL**: `{{base_url}}/health`
- **Headers**: None required
- **Body**: None

**Expected Response**:
```json
{
    "status": "ok",
    "service": "UltimaScraperAPI Wrapper",
    "timestamp": "2024-01-20T12:34:56.789Z"
}
```

### 2. Authentication
**Login with your cookies**

#### Option A: Using auth.json on server
- **Method**: `POST`
- **URL**: `{{base_url}}/auth`
- **Headers**: 
  ```
  Content-Type: application/json
  ```
- **Body**: None (will use auth.json)

#### Option B: Providing credentials
- **Method**: `POST`
- **URL**: `{{base_url}}/auth`
- **Headers**: 
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
  ```json
  {
      "auth": {
          "id": "123456789",
          "cookie": "auth_id=xxx; sess=yyy; auth_hash=zzz;",
          "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
          "x_bc": "optional_token_here"
      }
  }
  ```

**Expected Response**:
```json
{
    "success": true,
    "message": "Authentication successful",
    "user": {
        "id": "123456789",
        "username": "yourusername",
        "name": "Your Name"
    }
}
```

**Save to Environment**: In the Tests tab, add:
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("username", jsonData.user.username);
}
```

### 3. Get Current User Info
**Get authenticated user's information**

- **Method**: `GET`
- **URL**: `{{base_url}}/me`
- **Headers**: None required
- **Body**: None

**Expected Response**:
```json
{
    "id": "123456789",
    "username": "yourusername",
    "name": "Your Name",
    "email": "email@example.com",
    "avatar": "https://...",
    "bio": "Your bio text",
    "posts_count": 150,
    "photos_count": 100,
    "videos_count": 50,
    "is_verified": true
}
```

### 4. Get User Profile
**Get a specific user's profile**

- **Method**: `GET`
- **URL**: `{{base_url}}/user/targetusername`
- **Headers**: None required
- **Body**: None

**Expected Response**:
```json
{
    "id": "987654321",
    "username": "targetusername",
    "name": "Target User",
    "avatar": "https://...",
    "header": "https://...",
    "bio": "User's bio text",
    "posts_count": 250,
    "photos_count": 200,
    "videos_count": 50,
    "joined": "2020-01-15",
    "is_verified": true
}
```

### 5. Get User Posts
**Get posts from a user with pagination**

- **Method**: `GET`
- **URL**: `{{base_url}}/user/targetusername/posts?limit=10&offset=0`
- **Headers**: None required
- **Query Parameters**:
  ```
  limit: 10 (number of posts)
  offset: 0 (starting position)
  ```

**Expected Response**:
```json
{
    "posts": [
        {
            "id": "post123",
            "text": "Post content here...",
            "price": 0,
            "created_at": "2024-01-15T10:30:00Z",
            "likes_count": 156,
            "comments_count": 23,
            "is_pinned": false,
            "media": [
                {
                    "id": "media123",
                    "type": "photo",
                    "url": "https://...",
                    "preview": "https://..."
                }
            ]
        }
    ],
    "count": 10,
    "limit": 10,
    "offset": 0
}
```

### 6. Get Messages
**Get messages with a specific user**

- **Method**: `GET`
- **URL**: `{{base_url}}/user/targetusername/messages?limit=20`
- **Headers**: None required
- **Query Parameters**:
  ```
  limit: 20
  offset: 0
  ```

**Expected Response**:
```json
{
    "messages": [
        {
            "id": "msg123",
            "text": "Hello! Thanks for subscribing!",
            "price": 0,
            "created_at": "2024-01-20T09:15:00Z",
            "is_read": true,
            "is_from_user": true,
            "media": []
        }
    ],
    "count": 20,
    "limit": 20,
    "offset": 0
}
```

### 7. Get Stories
**Get stories from a user**

- **Method**: `GET`
- **URL**: `{{base_url}}/user/targetusername/stories`
- **Headers**: None required
- **Body**: None

**Expected Response**:
```json
{
    "stories": [
        {
            "id": "story123",
            "created_at": "2024-01-20T08:00:00Z",
            "expires_at": "2024-01-21T08:00:00Z",
            "is_viewed": false,
            "media": [
                {
                    "id": "media456",
                    "type": "photo",
                    "url": "https://...",
                    "preview": "https://..."
                }
            ]
        }
    ],
    "count": 3
}
```

### 8. Get Subscriptions
**Get your active subscriptions**

- **Method**: `GET`
- **URL**: `{{base_url}}/subscriptions?limit=50&offset=0`
- **Headers**: None required
- **Query Parameters**:
  ```
  limit: 50
  offset: 0
  ```

**Expected Response**:
```json
{
    "subscriptions": [
        {
            "id": "sub123",
            "username": "creator1",
            "name": "Creator Name",
            "avatar": "https://...",
            "is_verified": true,
            "subscription": {
                "price": 9.99,
                "status": "active",
                "expires_at": "2024-02-20T00:00:00Z",
                "renew": true
            }
        }
    ],
    "count": 25,
    "limit": 50,
    "offset": 0
}
```

## Postman Collection Setup

### 1. Create Request Folders
Organize your collection:
```
📁 UltimaScraperAPI
  📁 Authentication
    - Health Check
    - Login
    - Get Me
  📁 Users
    - Get User Profile
    - Get User Posts
    - Get User Messages
    - Get User Stories
  📁 Subscriptions
    - Get Subscriptions
```

### 2. Collection Variables
Set these in your collection:
```javascript
// Pre-request Script (Collection level)
pm.collectionVariables.set("timestamp", new Date().toISOString());
```

### 3. Tests for All Requests
Add to collection-level Tests:
```javascript
// Log response time
console.log(`Response time: ${pm.response.responseTime}ms`);

// Check for valid JSON
pm.test("Response is JSON", function () {
    pm.response.to.have.jsonBody();
});

// Check status code
pm.test("Status code is not 500", function () {
    pm.expect(pm.response.code).to.not.equal(500);
});
```

## Advanced Testing

### 1. Authentication Flow Test
Create a test that runs the full auth flow:
```javascript
// In Authentication request Tests tab
pm.test("Authentication successful", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.user).to.have.property('username');
    
    // Save for next requests
    pm.environment.set("auth_success", true);
    pm.environment.set("user_id", jsonData.user.id);
});
```

### 2. Pagination Test
Test pagination on posts endpoint:
```javascript
// Pre-request Script
pm.variables.set("limit", 5);
pm.variables.set("offset", 0);

// Tests
pm.test("Pagination works correctly", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.posts.length).to.be.at.most(5);
    pm.expect(jsonData.limit).to.equal(5);
    pm.expect(jsonData.offset).to.equal(0);
});
```

### 3. Error Handling Test
Test 404 response:
```javascript
// GET /api/user/nonexistentuser
pm.test("Returns 404 for non-existent user", function () {
    pm.response.to.have.status(404);
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('error');
});
```

## Postman Runner

### Run Collection Tests
1. Click "Runner" button
2. Select "UltimaScraperAPI" collection
3. Set environment to "UltimaScraperAPI Local"
4. Set iterations if needed
5. Click "Run UltimaScraperAPI"

### Test Sequence
```
1. Health Check → 2. Authenticate → 3. Get Me → 4. Get User → 5. Get Posts → etc.
```

## Export/Import Collection

### Export Collection
1. Right-click collection → Export
2. Choose Collection v2.1
3. Save as `UltimaScraperAPI.postman_collection.json`

### Share with Team
```json
{
    "info": {
        "name": "UltimaScraperAPI",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        // Your requests here
    ],
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:5000/api"
        }
    ]
}
```

## Tips

1. **Use Environment Variables**: Store base_url, usernames, and other dynamic values
2. **Add Tests**: Verify responses automatically
3. **Use Pre-request Scripts**: Set up data before requests
4. **Monitor API**: Use Postman Monitors for scheduled tests
5. **Generate Code**: Click "Code" to generate requests in various languages
6. **Save Examples**: Save response examples for documentation

## Common Issues

### 401 Unauthorized
- You need to call `/api/auth` first
- Check if cookies are still valid

### 404 Not Found  
- Check the username exists
- Verify the endpoint URL is correct

### 500 Server Error
- Check server logs
- Verify auth.json format
- Check if the library is properly installed

## Quick Test Flow
1. Start server: `python api_server.py`
2. Import this collection to Postman
3. Run Health Check
4. Run Authentication
5. Test other endpoints