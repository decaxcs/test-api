# Send Message Feature Documentation

## Overview

I've successfully implemented and fixed the **send_message** functionality for the OnlyFans API. This allows you to programmatically send messages to users, including free messages, paid messages, and messages with locked text.

**UPDATE**: Fixed the 400 Bad Request error by correcting the POST request to send JSON data properly.

## Implementation Details

### 1. **Core Method Added to UserModel**

Location: `ultima_scraper_api/apis/onlyfans/classes/user_model.py`

```python
async def send_message(
    self,
    text: str,
    price: int = 0,
    media_ids: list[int] | None = None,
    locked_text: bool = False,
) -> MessageModel | None:
```

### 2. **Parameters**

- **text** (str): The message text to send
- **price** (int): Price in cents (0 for free, e.g., 500 = $5.00)
- **media_ids** (list[int]): Optional list of media IDs to attach
- **locked_text** (bool): Whether the text should be locked until paid

### 3. **API Endpoint**

Uses the OnlyFans API endpoint:
```
POST /api2/v2/chats/{user_id}/messages
```

### 4. **Request Payload Structure**

```json
{
    "text": "Your message here",
    "lockedText": false,
    "mediaFiles": [],
    "price": 0,
    "isCouplePeopleMedia": false,
    "isForward": false
}
```

## Usage Examples

### Basic Usage - Send Free Message

```python
# Get the user
user = await authed.get_user("username")

# Send a free message
result = await user.send_message("Hello! How are you?")

if result:
    print(f"Message sent! ID: {result.id}")
```

### Send Paid Message

```python
# Send a message for $5.00 (price in cents)
result = await user.send_message(
    text="Exclusive content just for you!",
    price=500  # $5.00
)
```

### Send Message with Media

```python
# Send message with attached media
result = await user.send_message(
    text="Check out these photos!",
    media_ids=[12345, 67890]  # Media IDs from your uploads
)
```

### Send Message with Locked Text

```python
# Send message with locked text (text hidden until paid)
result = await user.send_message(
    text="Secret message - unlock to read!",
    price=300,  # $3.00
    locked_text=True
)
```

## Testing the Feature

### 1. **Using the Example Script**

Run the dedicated send message example:
```bash
python send_message_example.py
```

### 2. **Using the API Function Tester**

The send message feature has been added to the interactive tester:
```bash
python api_function_tester.py
```
Select option **17** from the menu.

## Return Value

The method returns a `MessageModel` object on success with properties:
- `id`: Message ID
- `text`: Message text
- `price`: Price in cents
- `created_at`: Creation timestamp
- `is_free`: Whether the message is free
- `is_tip`: Whether it's a tip message

Returns `None` if the message fails to send.

## Important Notes

1. **Authentication Required**: Your auth.json must have valid cookies
2. **Rate Limiting**: OnlyFans may limit how many messages you can send
3. **User Restrictions**: Some users may have messaging disabled
4. **Price Format**: Always use cents (multiply dollars by 100)
5. **Media Uploads**: Media IDs must be from previously uploaded content

## Error Handling

The method includes error handling and will:
- Log errors to the console/log file
- Return `None` on failure
- Not throw exceptions (caught internally)

## Security Considerations

- The method uses the existing authenticated session
- All requests are signed with the dynamic rules
- No credentials are exposed in the payload
- HTTPS is used for all communications

## Future Enhancements

Potential improvements could include:
- Bulk message sending
- Message scheduling
- Reply to specific messages
- Forward messages
- Delete/unsend messages
- Read receipts handling

## Troubleshooting

If messages fail to send:
1. Check your authentication is valid
2. Verify the recipient exists and accepts messages
3. Ensure price is in cents, not dollars
4. Check rate limiting hasn't been triggered
5. Review logs for specific error messages

This implementation provides a foundation for message automation while maintaining the security and structure of the existing codebase.