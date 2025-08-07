# New API Endpoints Guide

## Overview
This guide covers the new endpoints added to the FastAPI server and the fixes applied to existing endpoints.

## New Endpoints

### 1. Get All Messages from All Chats

#### Basic Version: `/api/messages/all`
- **Method**: GET
- **Description**: Fetches all messages from all your chats
- **Parameters**:
  - `limit_per_chat` (int, default: 50): Maximum messages to fetch per chat
  - `include_purchases` (bool, default: true): Include PPV/paid messages
- **Response**: 
```json
{
  "total_messages": 150,
  "total_chats": 5,
  "chat_summaries": [
    {
      "user_id": 123456,
      "username": "example_user",
      "name": "Example User",
      "message_count": 30
    }
  ],
  "messages": [
    {
      "id": 789,
      "text": "Hello!",
      "price": 0,
      "is_free": true,
      "created_at": "2025-01-07T10:30:00",
      "chat_user": {...},
      "media": [...]
    }
  ]
}
```

#### Advanced Version: `/api/messages/all/detailed`
- **Method**: GET
- **Description**: Fetches all messages with detailed statistics and advanced filtering
- **Parameters**:
  - `limit_per_chat` (int, default: 100, max: 200): Maximum messages per chat
  - `include_purchases` (bool, default: true): Include PPV messages
  - `include_tips` (bool, default: true): Include tip messages
  - `only_with_media` (bool, default: false): Only return messages with media
- **Response**: Includes detailed statistics, per-chat breakdowns, and filtered messages

### 2. Mass Send Messages

#### Basic Mass Send: `/api/messages/mass-send`
- **Method**: POST
- **Description**: Send a message to all your chats at once
- **Parameters**:
  - `test_mode` (bool, default: false): Preview recipients without sending
  - `exclude_usernames` (list[str], default: []): Usernames to exclude
- **Request Body**:
```json
{
  "text": "Hello everyone!",
  "media_ids": [],
  "price": 0,
  "locked_text": false
}
```
- **Response**:
```json
{
  "total_chats": 10,
  "successful_sends": 9,
  "failed_sends": 1,
  "test_mode": false,
  "results": [...],
  "summary": {
    "total_recipients": 10,
    "successful": 9,
    "failed": 1,
    "excluded": 0,
    "success_rate": "90.0%"
  }
}
```

#### Filtered Mass Send: `/api/messages/mass-send/filtered`
- **Method**: POST
- **Description**: Send messages with advanced filtering options
- **Parameters**:
  - `only_subscribed` (bool, default: false): Only send to subscribed users
  - `only_active_chats` (bool, default: false): Only send to recently active chats
  - `days_active` (int, default: 30): Define "active" as activity within X days
  - `test_mode` (bool, default: true): Test mode is ON by default for safety
  - `exclude_usernames` (list[str], default: []): Usernames to exclude
- **Request Body**: Same as basic mass send
- **Features**:
  - Smart filtering by subscription status
  - Activity-based filtering
  - Test mode enabled by default
  - Detailed filtering results

### 3. Get Specific Post: `/api/post/{post_id}`
- **Method**: GET
- **Description**: Get details of a specific post by ID
- **Parameters**: 
  - `post_id` (int, path): The post ID
- **Response**: Full post details from OnlyFans API

## Fixed Endpoints

### 1. Messages Endpoint (`/api/user/{username}/messages`)
**Fixes Applied**:
- Changed `offset` parameter to `offset_id` (correct for OnlyFans API)
- Added `url_picker` to generate proper media URLs
- Added all message properties (is_free, is_tip, is_opened, etc.)
- Added author information and user statistics
- Enhanced media handling with locked/viewable status

### 2. Posts Endpoint (`/api/user/{username}/posts`)
**Fixes Applied**:
- Changed from `offset` to `label` and `after_date` parameters
- Added handling for both dict and PostModel objects
- Enhanced media URL generation
- Added missing post properties (raw_text, is_archived, etc.)

### 3. Subscriptions Endpoint (`/api/subscriptions`)
**Fixes Applied**:
- Removed `offset` parameter
- Added `sub_type` (all, active, expired, attention) and `filter_by` parameters
- Fixed SubscriptionModel attribute access (uses user.id instead of subscription.id)
- Added expiration date and pricing information

### 4. Chats Endpoint (`/api/chats`)
**Fixes Applied**:
- Fixed ChatModel attribute access (uses chat.user for user info)
- Added last message details
- Added chat-specific properties (has_purchased_feed, count_pinned_messages)

### 5. Like/Unlike Endpoints (`/api/post/{post_id}/like`)
**Updates Applied**:
- Updated to use new OnlyFans favorites endpoint pattern
- Changed from `/api2/v2/posts/{id}/like` to `/api2/v2/posts/{id}/favorites/{user_id}`
- Added better error handling for 404 errors
- Added debugging information in responses

## Usage Examples

### Get all messages from all chats:
```bash
GET http://localhost:5000/api/messages/all?limit_per_chat=100
```

### Mass send a free message (test mode):
```bash
POST http://localhost:5000/api/messages/mass-send?test_mode=true
Content-Type: application/json

{
  "text": "Happy New Year everyone!",
  "media_ids": [],
  "price": 0,
  "locked_text": false
}
```

### Mass send to active subscribers only:
```bash
POST http://localhost:5000/api/messages/mass-send/filtered?only_subscribed=true&only_active_chats=true&days_active=7&test_mode=false
Content-Type: application/json

{
  "text": "Special offer for my active subscribers!",
  "media_ids": [123456],
  "price": 500,
  "locked_text": true
}
```

### Get messages with media only:
```bash
GET http://localhost:5000/api/messages/all/detailed?only_with_media=true&limit_per_chat=200
```

## Important Notes

1. **Rate Limiting**: Mass send endpoints include automatic delays between sends (0.5s for basic, 1s for filtered)
2. **Test Mode**: Always test with `test_mode=true` before actual sending
3. **Media IDs**: Must be pre-uploaded media IDs from OnlyFans
4. **Prices**: Always in cents (500 = $5.00)
5. **Authentication**: All endpoints require valid authentication via auth.json

## Error Handling

All endpoints return proper HTTP status codes:
- 200: Success
- 400: Bad request (invalid parameters)
- 401: Authentication required
- 404: Resource not found
- 500: Server error

Error responses include detailed messages to help troubleshooting.