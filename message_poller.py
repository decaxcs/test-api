#!/usr/bin/env python3
"""
Message Poller for OnlyFans
Continuously checks for new messages at specified intervals
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, List
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
        logging.FileHandler('message_poller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MessagePoller:
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
        self.last_message_ids: Dict[int, str] = {}  # user_id: last_message_id
        self.state_file = Path("poller_state.json")
        
    def load_state(self):
        """Load the last known message IDs from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.last_message_ids = json.load(f)
                logger.info(f"Loaded state for {len(self.last_message_ids)} users")
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
    
    def save_state(self):
        """Save current message IDs to state file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.last_message_ids, f)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    async def get_chat_users(self, authed_user) -> List[UserModel]:
        """Get list of users to check for messages"""
        try:
            if self.specific_users:
                # Get specific users
                users = []
                for username in self.specific_users:
                    user = await authed_user.get_user(username)
                    if user:
                        users.append(user)
                    else:
                        logger.warning(f"Could not find user: {username}")
                return users
            else:
                # Get all users with active chats
                logger.info("Getting list of all chat users...")
                chats = await authed_user.get_chats()
                users = []
                
                for chat in chats:
                    # Extract user from chat
                    if hasattr(chat, 'with_user'):
                        users.append(chat.with_user)
                    elif hasattr(chat, 'user'):
                        users.append(chat.user)
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting chat users: {e}")
            return []
    
    async def check_user_messages(self, user: UserModel) -> List[MessageModel]:
        """Check for new messages from a specific user"""
        try:
            user_id = str(user.id)
            logger.debug(f"Checking messages from {user.username} (ID: {user_id})")
            
            # Get recent messages
            messages = await user.get_messages(limit=10)
            
            if not messages:
                return []
            
            new_messages = []
            latest_message_id = None
            
            # If this is the first time checking this user, initialize with the latest message
            if user_id not in self.last_message_ids:
                if messages:
                    self.last_message_ids[user_id] = str(messages[0].id)
                    logger.info(f"Initialized tracking for {user.username} with message ID: {messages[0].id}")
                return []  # Don't report existing messages as new on first check
            
            for message in messages:
                message_id = str(message.id)
                
                # Track the latest message ID
                if latest_message_id is None:
                    latest_message_id = message_id
                
                # Check if this is a new message
                if message_id == self.last_message_ids[user_id]:
                    # We've seen this message before, stop checking older ones
                    break
                new_messages.append(message)
            
            # Update the last seen message ID
            if latest_message_id:
                self.last_message_ids[user_id] = latest_message_id
            
            return list(reversed(new_messages))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Error checking messages from {user.username}: {e}")
            return []
    
    def format_message(self, message: MessageModel, user: UserModel) -> str:
        """Format a message for display"""
        try:
            # Get message details
            text = getattr(message, 'text', '')
            created_at = getattr(message, 'created_at', datetime.now())
            # Check if message is from the authenticated user (me) or the other user
            authed_user = user.get_authed().user
            is_from_user = message.fromUser.id == authed_user.id if hasattr(message, 'fromUser') else False
            
            # Format timestamp
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            sender = "You" if is_from_user else user.username
            
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
            logger.info("Starting polling cycle...")
            users = await self.get_chat_users(authed_user)
            
            if not users:
                logger.warning("No users to check")
                return
            
            logger.info(f"Checking messages from {len(users)} users")
            total_new_messages = 0
            
            for user in users:
                new_messages = await self.check_user_messages(user)
                
                if new_messages:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"NEW MESSAGES from {user.username}:")
                    logger.info(f"{'='*60}")
                    
                    for message in new_messages:
                        formatted = self.format_message(message, user)
                        logger.info(formatted)
                    
                    logger.info(f"{'='*60}\n")
                    total_new_messages += len(new_messages)
                
                # Small delay between users to avoid rate limiting
                await asyncio.sleep(1)
            
            if total_new_messages > 0:
                logger.info(f"Found {total_new_messages} new message(s) total")
            else:
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
                        logger.info(f"Waiting {self.check_interval} seconds until next check...")
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
    
    parser = argparse.ArgumentParser(description="Poll OnlyFans for new messages")
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
        state_file = Path("poller_state.json")
        if state_file.exists():
            state_file.unlink()
            logger.info("Reset saved state")
    
    # Create and run poller
    poller = MessagePoller(
        check_interval_seconds=args.interval,
        specific_users=args.users
    )
    
    await poller.run()


if __name__ == "__main__":
    asyncio.run(main())