# UltimaScraperAPI - Clean Structure

## Essential Files Only

### 🔑 Core Files
- **auth.json** - Your authentication credentials (DO NOT SHARE!)
- **api_server.py** - Flask REST API server
- **ultima_scraper_api/** - Main library code

### 📚 Key Documentation
- **ULTIMATE_API_CHEATSHEET.md** - Complete guide with all examples
- **API_ENDPOINT_MAPPING.md** - Full API endpoint reference
- **CLAUDE.md** - Codebase guidance for AI assistants

### 🛠️ Main Scripts
- **send_message_example.py** - Send messages to users
- **message_reply_example.py** - Reply to messages
- **fetch_all_messages_to_json.py** - Export messages to JSON
- **fetch_all_messages_with_media.py** - Export with media analysis
- **analyze_ppv_messages.py** - Analyze pay-per-view content

### 📁 Folders
- **ultima_scraper_api/** - Core library (DO NOT MODIFY)
- **logs/** - Log files (auto-generated)
- **_dump/** - Archived test files and old docs

## Quick Start

1. **Setup auth.json**:
```json
{
  "auth": {
    "id": YOUR_USER_ID,
    "cookie": "YOUR_FULL_COOKIE_STRING",
    "x_bc": "YOUR_X_BC_TOKEN",
    "user_agent": "YOUR_BROWSER_USER_AGENT"
  }
}
```

2. **Run API Server**:
```bash
python api_server.py
```

3. **Or use directly**:
```python
import asyncio
from ultima_scraper_api import OnlyFansAPI

async def main():
    api = OnlyFansAPI()
    authed = await api.login(auth_json)
    user = await authed.get_user("username")
    posts = await user.get_posts()

asyncio.run(main())
```

## What Was Cleaned Up

Moved to `_dump/` folder:
- Test scripts (test_*.py, debug_*.py)
- Example files (example_*.py)
- Duplicate documentation
- Old log files
- Redundant config examples

Keep the dump folder if you need to reference old code, or delete it to save space.