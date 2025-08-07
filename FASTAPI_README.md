# FastAPI Server for UltimaScraperAPI

## Overview

This is a proper async-compatible API server built with FastAPI that resolves the event loop issues encountered with the Flask implementation.

## Why FastAPI?

The original Flask server had fundamental incompatibility issues between Flask's synchronous nature and the UltimaScraperAPI's asynchronous operations. This caused "Event loop is closed" errors when trying to fetch messages.

FastAPI natively supports async/await operations, making it the perfect choice for this API.

## Installation

1. First, install FastAPI dependencies:
```bash
python install_fastapi.py
```

Or manually install:
```bash
pip install fastapi uvicorn[standard] python-multipart pydantic
```

2. Make sure you have your `auth.json` file configured

## Running the Server

```bash
python api_server_fastapi.py
```

The server will start on `http://localhost:5000`

## Key Features

1. **Native Async Support**: No more event loop errors!
2. **Interactive Documentation**: Visit `http://localhost:5000/docs` for Swagger UI
3. **Type Safety**: Uses Pydantic models for request/response validation
4. **Better Error Handling**: Proper HTTP exceptions with detailed error messages
5. **CORS Enabled**: Works with any frontend application

## API Endpoints

- `POST /api/auth` - Authenticate with OnlyFans
- `GET /api/me` - Get current user info
- `GET /api/user/{username}` - Get user profile
- `GET /api/user/{username}/posts` - Get user posts
- `GET /api/user/{username}/messages` - Get messages (THIS NOW WORKS!)
- `GET /api/user/{username}/stories` - Get user stories
- `GET /api/subscriptions` - Get your subscriptions

## Testing with Postman

Same workflow as before:
1. POST to `/api/auth` with your auth.json content
2. Use any other endpoint - the session is maintained server-side

## Differences from Flask Version

1. **No async_route decorator needed** - FastAPI handles async natively
2. **Automatic API documentation** - Visit `/docs` for interactive testing
3. **Better dependency injection** - Authentication is handled via FastAPI's Depends
4. **Proper async context management** - No more event loop conflicts

## Example Usage

```python
import requests

# Authenticate
auth_data = {
    "auth": {
        "id": 513665682,
        "cookie": "your_cookie_string",
        "x_bc": "your_x_bc",
        "user_agent": "your_user_agent"
    }
}

response = requests.post("http://localhost:5000/api/auth", json=auth_data)
print(response.json())

# Get messages (this now works!)
messages = requests.get("http://localhost:5000/api/user/heyitsmilliexx/messages")
print(messages.json())
```

## Troubleshooting

If you encounter any issues:
1. Make sure all dependencies are installed
2. Check that your auth.json is valid
3. Look at the server console for detailed error messages
4. The server automatically reloads on code changes

This FastAPI implementation completely resolves the asyncio issues and provides a much more robust API server for the UltimaScraperAPI.