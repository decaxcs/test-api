# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UltimaScraperAPI is a Python library providing programmatic read-only access to OnlyFans and Fansly platforms. It's designed for fetching content, messages, posts, and user data through cookie-based authentication.

## Development Commands

### Running the FastAPI Server
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the FastAPI server
python api_server_fastapi.py

# Server runs on http://localhost:5000
# API documentation available at http://localhost:5000/docs
```

### Installation and Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt  # For FastAPI server

# Create auth.json from template
cp auth.json.example auth.json
# Edit auth.json with your OnlyFans cookies
```

### Code Quality
```bash
# Format code with Black
black ultima_scraper_api/

# Type checking with mypy
mypy ultima_scraper_api/

# Lint and typecheck FastAPI server
black api_server_fastapi.py
mypy api_server_fastapi.py
```

### Testing
```bash
# Test authentication
python _dump/test_files/test_auth_simple.py

# Debug authentication issues
python _dump/test_files/debug_auth.py
python _dump/test_files/trace_auth.py

# Test API endpoints
python _dump/test_files/api_function_tester.py

# Test message sending
python _dump/test_files/test_send_simple.py
```

## Architecture Overview

### Core Module Structure
- **ultima_scraper_api/apis/** - Platform-specific API implementations
  - **onlyfans/** - OnlyFans API with authenticator, models, and decorators
    - **classes/** - Model classes (UserModel, PostModel, MessageModel, etc.)
    - **authenticator.py** - Handles cookie-based authentication
  - **fansly/** - Fansly API with identical structure
- **ultima_scraper_api/managers/** - Session management and scraping coordination
- **api_server_fastapi.py** - FastAPI REST wrapper exposing library functionality

### Key Design Patterns
1. **Async/Await**: All API calls are asynchronous for concurrent operations
2. **Model Methods**: Models contain their own data fetching logic (e.g., `user.get_posts()`)
3. **Session Management**: Centralized in SessionManager with rate limiting and retry logic
4. **Error Handling**: Consistent error wrapping with detailed context

### Authentication Flow
1. Load credentials from `auth.json` containing cookies and headers
2. FastAPI server authenticates on startup using `OnlyFansAPI.login()`
3. All endpoints use `Depends(require_auth)` to ensure authentication
4. Session headers include dynamic request signing for OnlyFans

### Important Files
- **auth.json** - Cookie-based authentication credentials (never commit)
- **api_server_fastapi.py** - Main FastAPI server with all REST endpoints
- **ultima_scraper_api/apis/onlyfans/classes/extras.py** - OnlyFans API endpoint definitions
- **working_api_endpoints_v3.csv** - Documentation of all working endpoints

## Common Development Tasks

### Adding New FastAPI Endpoints
1. Find the corresponding method in `ultima_scraper_api/apis/onlyfans/classes/`
2. Add endpoint in `api_server_fastapi.py` following existing patterns:
   ```python
   @app.get("/api/endpoint")
   async def endpoint_name(params, authed_instance=Depends(require_auth)):
       # Call UltimaScraperAPI method
       # Handle response formatting
       # Return JSON response
   ```
3. Handle both dict and object responses (many methods return either)
4. Use proper parameter types (e.g., `offset_id` not `offset` for messages)

### Debugging Authentication Issues
1. Check auth.json has all required fields: `auth_id`, `cookie`, `x_bc`, `user_agent`
2. Ensure cookies are fresh (OnlyFans cookies expire)
3. Check logs in `logs/` directory
4. Use `debug_auth.py` to verify auth structure

### Working with OnlyFans API Quirks
- Messages use `offset_id` for pagination, not `offset`
- Posts use `label` and `after_date` parameters, not `offset`
- Media URLs require `url_picker()` method to generate signed URLs
- Like/unlike uses `/favorites/` endpoint, not `/like`
- Many models store user info in a nested `user` attribute

### FastAPI Response Patterns
- Always check if response is dict or model object
- Use `getattr()` for optional attributes
- Include proper error handling with HTTPException
- Return consistent response structures with counts and metadata

## API Endpoint Categories

### Working Endpoints
- Authentication: `/api/auth`, `/api/me`
- User Info: `/api/user/{username}`, `/api/user/{username}/posts`, etc.
- Messages: `/api/messages/all`, `/api/messages/mass-send`
- Financial: `/api/transactions`, `/api/paid-content`
- Content: Posts, stories, highlights, vault

### Methods Available but Not Exposed
- `user.buy_subscription()` - Subscribe to a user
- `post.buy_ppv()` - Purchase pay-per-view content
- `user.search_chat()` - Search within conversations
- `post.get_comments()` - Fetch post comments
- See full list in codebase analysis

## Error Handling
- FastAPI returns proper HTTP status codes
- Detailed error messages in response body
- Automatic retry logic in SessionManager
- Rate limiting handled transparently

## Security Considerations
- Read-only API - no content creation methods exposed
- Cookie-based auth only - no password handling
- Never commit auth.json
- All requests use HTTPS
- Request signing prevents tampering