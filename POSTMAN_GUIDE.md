# Postman Guide for UltimaScraperAPI

## Setup

1. **Base URL**: `http://127.0.0.1:5000`

## Step 1: Authenticate First (Required!)

### POST /api/auth
- **Method**: POST
- **URL**: `http://127.0.0.1:5000/api/auth`
- **Headers**: 
  - `Content-Type: application/json`
- **Body** (raw JSON):
```json
{
  "auth": {
    "id": 513665682,
    "cookie": "YOUR_FULL_COOKIE_STRING",
    "x_bc": "YOUR_X_BC_VALUE",
    "user_agent": "YOUR_USER_AGENT"
  }
}
```

**Note**: The server maintains session state, so you only need to authenticate once per server session.

## Step 2: Test Authentication

### GET /api/me
- **Method**: GET
- **URL**: `http://127.0.0.1:5000/api/me`
- **Headers**: None needed (session is maintained server-side)

## Step 3: Get Messages

### GET /api/user/{username}/messages

**Basic call (your example):**
- **Method**: GET
- **URL**: `http://127.0.0.1:5000/api/user/heyitsmilliexx/messages`
- **Headers**: None needed
- **Query Parameters** (optional):
  - `limit`: Number of messages (default: 50)
  - `offset_id`: Message ID to start from for pagination (optional)

**Examples:**
1. No parameters (gets 50 most recent):
   ```
   http://127.0.0.1:5000/api/user/heyitsmilliexx/messages
   ```

2. Get 10 messages:
   ```
   http://127.0.0.1:5000/api/user/heyitsmilliexx/messages?limit=10
   ```

3. Get next page (use last_message_id from previous response):
   ```
   http://127.0.0.1:5000/api/user/heyitsmilliexx/messages?limit=50&offset_id=123456789
   ```

## Common Issues & Solutions

### 1. Getting 401 Unauthorized
- **Solution**: You need to call `/api/auth` first
- The server needs to maintain your session

### 2. Getting 404 User not found
- **Solution**: Check the username spelling
- User might not exist or be blocked

### 3. Getting 500 Internal Server Error
- **Solution**: Check server console for detailed error
- Might be the asyncio issue (use the fixed version)

### 4. Request hangs/times out
- **Solution**: This is likely the asyncio error
- The server is stuck in the async loop
- Restart server and use the fixed version

## Complete Postman Collection

### Collection Variables:
```
base_url: http://127.0.0.1:5000
username: heyitsmilliexx
```

### Request Examples:

1. **Authenticate**
   - POST `{{base_url}}/api/auth`
   - Body: Your auth.json content

2. **Check Auth**
   - GET `{{base_url}}/api/me`

3. **Get User**
   - GET `{{base_url}}/api/user/{{username}}`

4. **Get Messages**
   - GET `{{base_url}}/api/user/{{username}}/messages`

5. **Get Posts**
   - GET `{{base_url}}/api/user/{{username}}/posts?limit=10`

6. **Get Stories**
   - GET `{{base_url}}/api/user/{{username}}/stories`

## Testing Script

You can also use the test script:
```bash
python test_messages_api.py
```

This will test all endpoints and show you exactly what's happening.