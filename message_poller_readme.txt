Message Poller for OnlyFans
==========================

This script continuously checks for new messages at regular intervals.

USAGE:
------
python message_poller.py [options]

OPTIONS:
--------
-i, --interval SECONDS    Check interval in seconds (default: 60)
-u, --users USER1 USER2   Monitor specific users only (default: all)
--reset                   Clear saved state and start fresh

EXAMPLES:
---------
# Check every 60 seconds (default)
python message_poller.py

# Check every 30 seconds
python message_poller.py -i 30

# Monitor specific users only
python message_poller.py -u username1 username2

# Reset state and check every 2 minutes
python message_poller.py --reset -i 120

FEATURES:
---------
- Saves state between runs (remembers last seen messages)
- Shows sender, timestamp, text, media count, and tips
- Logs to both console and message_poller.log file
- Handles errors gracefully and continues polling
- Can be stopped safely with Ctrl+C

NOTES:
------
- First run won't show any messages as "new" (establishing baseline)
- State is saved in poller_state.json
- Requires auth.json with valid OnlyFans credentials
- Uses the same authentication as other scripts in this project