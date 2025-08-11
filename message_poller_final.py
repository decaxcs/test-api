#!/usr/bin/env python3
"""
Message Poller Final - Works around cache issues by using direct API calls
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
from pathlib import Path

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from ultima_scraper_api.apis.onlyfans.classes.user_model import UserModel
from ultima_scraper_api.apis.onlyfans.classes.message_model import MessageModel


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('message_poller_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MessagePollerFinal:
    def __init__(self, check_interval_seconds: int = 60, 
                 specific_users: Optional[List[str]] = None):
        """
        Initialize the message poller
        
        Args:
            check_interval_seconds: How often to check for new messages (default: 60 seconds)
            specific_users: List of specific usernames to monitor (None = all users)
        """
        self.check_interval = check_interval_seconds
        self.specific_users = specific_users
        self.api: Optional[OnlyFansAPI] = None
        # Store last message info: user_id -> (message_id, text, created_at)
        self.last_message_info: Dict[str, Tuple[str, str, str]] = {}
        self.state_file = Path("poller_state_final.json")
        
    def load_state(self):
        """Load the last known message info from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.last_message_info = json.load(f)
                logger.info(f"Loaded state for {len(self.last_message_info)} users")
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
    
    def save_state(self):
        """Save current message info to state file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.last_message_info, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def format_message_log(self, message: MessageModel, user: UserModel, authed_user) -> str:
        """Format a message for logging"""
        try:
            text = getattr(message, 'text', '')
            created_at = getattr(message, 'created_at', datetime.now())
            
            # Check if message is from the authenticated user (me) or the other user
            is_from_me = message.fromUser.id == authed_user.user.id if hasattr(message, 'fromUser') else False
            sender = "ME" if is_from_me else user.username
            
            # Format timestamp
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # Truncate long messages
            if text and len(text) > 100:
                text = text[:100] + "..."
            
            return f"[{created_at.strftime('%Y-%m-%d %H:%M:%S')}] {sender}: {text} (ID: {message.id})"
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"[Error formatting message ID: {message.id}]"
    
    async def get_messages_direct(self, user: UserModel, limit: int = 10) -> List[MessageModel]:
        """Get messages using direct API call to bypass cache"""
        try:
            # Force cache to be "old" by setting it to None
            if hasattr(user, 'cache') and hasattr(user.cache, 'messages'):
                user.cache.messages.processed_at = None
                user.cache.messages.released_at = None
            
            # Clear any existing scraped messages
            if hasattr(user, 'scrape_manager'):
                user.scrape_manager.scraped.Messages.clear()
            
            # Get messages - this should now make a fresh API call
            messages = await user.get_messages(limit=limit)
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages directly: {e}")
            return []
    
    async def check_user_messages(self, user: UserModel, authed_user) -> List[MessageModel]:
        """Check for new messages from a specific user"""
        try:
            user_id = str(user.id)
            logger.debug(f"Checking messages from {user.username} (ID: {user_id})")
            
            # Get recent messages using direct method
            messages = await self.get_messages_direct(user, limit=10)
            
            if not messages:
                logger.debug(f"  No messages found for {user.username}")
                return []
            
            # Just log the count at debug level
            logger.debug(f"  Fetched {len(messages)} messages")
            
            # Get the latest message info
            latest_msg = messages[0]
            latest_id = str(latest_msg.id)
            latest_text = getattr(latest_msg, 'text', '')
            latest_created = str(getattr(latest_msg, 'created_at', ''))
            
            # Check if we have previous info for this user
            if user_id not in self.last_message_info:
                # First time checking this user
                logger.debug(f"  First time checking {user.username}, initializing state")
                self.last_message_info[user_id] = [latest_id, latest_text, latest_created]
                return []
            
            # Compare with last known message
            last_id, last_text, last_created = self.last_message_info[user_id]
            
            if latest_id == last_id:
                logger.debug(f"  No new messages (latest ID still: {latest_id})")
                return []
            
            # Find all new messages (only from the other user, not from me)
            new_messages = []
            for msg in messages:
                if str(msg.id) == last_id:
                    break
                # Only include messages from the other user (not from me)
                is_from_me = msg.fromUser.id == authed_user.user.id if hasattr(msg, 'fromUser') else False
                if not is_from_me:
                    new_messages.append(msg)
            
            # Update state with latest message info
            self.last_message_info[user_id] = [latest_id, latest_text, latest_created]
            
            if len(new_messages) > 0:
                logger.info(f"  Found {len(new_messages)} NEW messages from {user.username}!")
            
            return list(reversed(new_messages))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Error checking messages from {user.username}: {e}")
            return []
    
    def format_new_message(self, message: MessageModel, user: UserModel, authed_user) -> str:
        """Format a new message for display"""
        try:
            # Get message details
            text = getattr(message, 'text', '')
            created_at = getattr(message, 'created_at', datetime.now())
            
            # Check if message is from the authenticated user (me) or the other user
            is_from_me = message.fromUser.id == authed_user.user.id if hasattr(message, 'fromUser') else False
            
            # Format timestamp
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            sender = "You" if is_from_me else user.username
            
            # Check for media
            media_count = 0
            if hasattr(message, 'media') and message.media:
                media_count = len(message.media)
            
            # Build message string
            msg_parts = [f"[{created_at.strftime('%Y-%m-%d %H:%M:%S')}] {sender}:"]
            
            if text:
                msg_parts.append(f'"{text}"')
            
            if media_count > 0:
                msg_parts.append(f"[{media_count} media file(s)]")
            
            # Check for tip
            if hasattr(message, 'price') and message.price and message.price > 0:
                msg_parts.append(f"[💰 ${message.price}]")
            
            return " ".join(msg_parts)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"[Error formatting message from {user.username}]"
    
    async def poll_once(self, authed_user):
        """Perform one polling cycle"""
        try:
            logger.debug("Starting polling cycle...")
            
            # Get list of users to check
            users_to_check = []
            
            if self.specific_users:
                # Get specific users
                for username in self.specific_users:
                    user = await authed_user.get_user(username)
                    if user:
                        users_to_check.append(user)
                    else:
                        logger.warning(f"Could not find user: {username}")
            else:
                # Get all chat users
                logger.debug("Getting list of all chat users...")
                chats = await authed_user.get_chats()
                
                for chat in chats:
                    # Extract user from chat
                    if hasattr(chat, 'with_user') and chat.with_user:
                        users_to_check.append(chat.with_user)
                    elif hasattr(chat, 'user') and chat.user:
                        users_to_check.append(chat.user)
            
            if not users_to_check:
                logger.warning("No users to check")
                return
            
            logger.info(f"Checking messages from {len(users_to_check)} users...")
            total_new_messages = 0
            
            for user in users_to_check:
                new_messages = await self.check_user_messages(user, authed_user)
                
                if new_messages:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔔 NEW MESSAGES from {user.username}:")
                    logger.info(f"{'='*60}")
                    
                    for message in new_messages:
                        formatted = self.format_new_message(message, user, authed_user)
                        logger.info(formatted)
                    
                    logger.info(f"{'='*60}")
                    total_new_messages += len(new_messages)
                
                # Small delay between users to avoid rate limiting
                await asyncio.sleep(1)
            
            if total_new_messages == 0:
                logger.info("No new messages found")
            
            # Save state after each cycle
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error during polling cycle: {e}")
    
    async def run(self):
        """Run the message poller continuously"""
        try:
            # Load auth details
            auth_file = Path("auth.json")
            if not auth_file.exists():
                raise FileNotFoundError("auth.json not found. Please create it with your credentials.")
            
            with open(auth_file, 'r') as f:
                auth_data = json.load(f)
            
            # Get auth details from the file
            auth_details = auth_data.get("auth", auth_data)
            
            # Create API instance
            self.api = OnlyFansAPI(UltimaScraperAPIConfig())
            
            # Load previous state
            self.load_state()
            
            # Authenticate and run polling loop
            logger.info("Authenticating with OnlyFans...")
            async with self.api.login_context(auth_json=auth_details) as authed:
                if not authed or not authed.is_authed():
                    raise Exception("Failed to authenticate with OnlyFans")
                
                if hasattr(authed, 'user') and authed.user:
                    logger.info(f"Successfully authenticated as: {authed.user.username}")
                else:
                    logger.info("Successfully authenticated")
                
                logger.info(f"Starting message poller (checking every {self.check_interval} seconds)")
                logger.info("Press Ctrl+C to stop")
                
                try:
                    while True:
                        await self.poll_once(authed)
                        logger.debug(f"Waiting {self.check_interval} seconds until next check...")
                        await asyncio.sleep(self.check_interval)
                        
                except KeyboardInterrupt:
                    logger.info("\nStopping message poller...")
                    self.save_state()
                    
        except Exception as e:
            logger.error(f"Error: {e}")
            self.save_state()
            raise


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Poll OnlyFans for new messages (Final)")
    parser.add_argument(
        "-i", "--interval", 
        type=int, 
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "-u", "--users",
        nargs="+",
        help="Specific usernames to monitor (default: all users)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the saved state and start fresh"
    )
    
    args = parser.parse_args()
    
    # Reset state if requested
    if args.reset:
        state_file = Path("poller_state_final.json")
        if state_file.exists():
            state_file.unlink()
            logger.info("Reset saved state")
    
    # Create and run poller
    poller = MessagePollerFinal(
        check_interval_seconds=args.interval,
        specific_users=args.users
    )
    
    await poller.run()


if __name__ == "__main__":
    asyncio.run(main())