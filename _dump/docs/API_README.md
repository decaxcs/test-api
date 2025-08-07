# UltimaScraperAPI Flask Wrapper

A REST API wrapper for UltimaScraperAPI that provides HTTP endpoints to access OnlyFans/Fansly data.

## Setup

1. **Install dependencies:**
```bash
# Install the main library dependencies
pip install -r requirements.txt

# Install Flask API dependencies
pip install -r requirements-api.txt
```

2. **Configure authentication:**
Create an `auth.json` file with your cookies:
```json
{
  "auth": {
    "id": "your_user_id",
    "cookie": "your_cookie_string",
    "user_agent": "your_browser_user_agent",
    "x_bc": "optional_token"
  }
}
```

3. **Run the server:**
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication
**POST** `/api/auth`
- Authenticate with OnlyFans using auth.json or provided credentials
- Body (optional): `{"auth": {...}}` or auth details will be read from auth.json

### User Information
**GET** `/api/me`
- Get current authenticated user information

**GET** `/api/user/<username>`
- Get profile information for a specific user

### Content
**GET** `/api/user/<username>/posts`
- Get posts from a user
- Query params: `limit` (default: 50), `offset` (default: 0)

**GET** `/api/user/<username>/messages`
- Get messages with a user
- Query params: `limit` (default: 50), `offset` (default: 0)

**GET** `/api/user/<username>/stories`
- Get stories from a user

### Subscriptions
**GET** `/api/subscriptions`
- Get your active subscriptions
- Query params: `limit` (default: 50), `offset` (default: 0)

### Health Check
**GET** `/api/health`
- Check if the API is running

## Example Usage

### Using curl:
```bash
# Authenticate
curl -X POST http://localhost:5000/api/auth

# Get user info
curl http://localhost:5000/api/user/username

# Get posts
curl http://localhost:5000/api/user/username/posts?limit=10
```

### Using Python requests:
```python
import requests

# Authenticate
resp = requests.post('http://localhost:5000/api/auth')

# Get user posts
resp = requests.get('http://localhost:5000/api/user/username/posts')
posts = resp.json()
```

### Using JavaScript:
```javascript
// Authenticate
await fetch('http://localhost:5000/api/auth', {method: 'POST'});

// Get user info
const response = await fetch('http://localhost:5000/api/user/username');
const user = await response.json();
```

## Production Deployment

For production, use gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

## Notes
- All endpoints require authentication except `/api/health`
- The API maintains a single authenticated session
- CORS is enabled for all origins (customize in production)
- Responses are in JSON format
- Error responses include error messages and status codes

## Security
- Never expose your auth.json file
- Use HTTPS in production
- Consider adding API key authentication
- Implement rate limiting for production use