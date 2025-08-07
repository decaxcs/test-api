#!/usr/bin/env python3
"""
OnlyFans API Function Tester
Interactive script to test all available API functions
"""

import asyncio
import orjson
import logging
from pathlib import Path
from datetime import datetime
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from logging_config import setup_logging, get_logger

# Setup logging with file handler
def setup_test_logging():
    """Setup logging for the tester with file output"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"api_tester_{timestamp}.log"
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler - INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                     datefmt='%H:%M:%S')
    console_handler.setFormatter(console_format)
    
    # File handler - DEBUG level (more detailed)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger, log_file

# Setup logging
logger, log_file_path = setup_test_logging()


class APIFunctionTester:
    def __init__(self):
        self.config = UltimaScraperAPIConfig()
        self.api = None  # Will be initialized in async context
        self.authed = None
        self.current_user = None
        self.test_count = 0  # Track number of tests run
        self.error_count = 0  # Track errors
        
    async def initialize(self):
        """Initialize API and authenticate"""
        logger.info("Starting API initialization...")
        
        # Initialize API in async context
        logger.debug("Creating OnlyFansAPI instance")
        self.api = OnlyFansAPI(self.config)
        
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json file not found!")
            return False
            
        logger.debug(f"Loading auth.json from: {auth_path.absolute()}")
        auth_json = orjson.loads(auth_path.read_bytes())
        logger.debug(f"Auth JSON loaded with user ID: {auth_json['auth'].get('id', 'N/A')}")
        
        logger.info("Attempting authentication...")
        self.authed = await self.api.login(auth_json["auth"])
        
        if not self.authed or not self.authed.is_authed():
            logger.error("Authentication failed!")
            return False
            
        logger.info("✓ Authentication successful")
        logger.debug(f"Authenticated user ID: {self.authed.id}")
        return True
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("OnlyFans API Function Tester")
        print("="*60)
        print("\n--- USER FUNCTIONS ---")
        print("1. Get User Info")
        print("2. Get Posts (timeline/archived)")
        print("3. Get Messages")
        print("4. Get Stories")
        print("5. Get Highlights")
        print("6. Search Messages")
        print("7. Get Mass Messages")
        
        print("\n--- SUBSCRIPTION FUNCTIONS ---")
        print("8. Get My Subscriptions")
        print("9. Get Subscription Price")
        
        print("\n--- CONTENT FUNCTIONS ---")
        print("10. Get Paid Content")
        print("11. Get Comments on Post")
        print("12. Get Chats List")
        print("13. Get Vault Lists")
        
        print("\n--- INTERACTION FUNCTIONS ---")
        print("14. Like/Unlike Content")
        print("15. Favorite Post")
        print("16. Block/Unblock User")
        print("17. Send Message (NEW!)")
        
        print("\n--- ACCOUNT FUNCTIONS ---")
        print("18. Get My Lists")
        print("19. Get Transactions")
        print("20. Get Login Issues")
        print("21. Get Blacklist")
        
        print("\n--- ADVANCED FUNCTIONS ---")
        print("22. Get Specific Post by ID")
        print("23. Get Specific Message by ID")
        print("24. Get User's Social Links")
        print("25. Get Promotions")
        
        print("\n0. Exit")
        print("-"*60)
    
    async def get_user_input(self, prompt="Enter username: "):
        """Get user input for username"""
        username = input(prompt).strip()
        logger.debug(f"User input received: {username}")
        
        if not username:
            logger.warning("Empty username provided")
            return None
            
        logger.info(f"Fetching user: {username}")
        user = await self.authed.get_user(username)
        
        if not user:
            logger.error(f"User '{username}' not found")
            print(f"❌ User '{username}' not found")
            return None
            
        self.current_user = user
        logger.info(f"✓ Found user: {user.username} (ID: {user.id})")
        logger.debug(f"User details - Posts: {user.posts_count}, Media: {user.medias_count}")
        print(f"✓ Found user: {user.username} (ID: {user.id})")
        return user
    
    async def test_get_user_info(self):
        """Test getting user info"""
        logger.info("Testing: Get User Info")
        user = await self.get_user_input()
        if not user:
            return
            
        logger.debug("Retrieving detailed user information")
        user_data = {
            "username": user.username,
            "name": user.name,
            "id": user.id,
            "posts_count": user.posts_count,
            "archived_posts_count": user.archived_posts_count,
            "photos_count": user.photos_count,
            "videos_count": user.videos_count,
            "audios_count": user.audios_count,
            "medias_count": user.medias_count,
            "is_performer": user.is_performer(),
            "subscription_price": user.subscription_price()
        }
        logger.debug(f"User data retrieved: {user_data}")
        
        print(f"\n--- User Info ---")
        print(f"Username: {user.username}")
        print(f"Name: {user.name}")
        print(f"ID: {user.id}")
        print(f"About: {user.about[:100]}..." if user.about and len(user.about) > 100 else f"About: {user.about}")
        print(f"Posts Count: {user.posts_count}")
        print(f"Archived Posts Count: {user.archived_posts_count}")
        print(f"Photos Count: {user.photos_count}")
        print(f"Videos Count: {user.videos_count}")
        print(f"Audios Count: {user.audios_count}")
        print(f"Total Media Count: {user.medias_count}")
        print(f"Is Performer: {user.is_performer()}")
        print(f"Subscription Price: ${user.subscription_price()}")
        print(f"Location: {getattr(user, 'location', 'N/A')}")
        print(f"Website: {getattr(user, 'website', 'N/A')}")
        
        logger.info("User info display completed")
    
    async def test_get_posts(self):
        """Test getting posts"""
        logger.info("Testing: Get Posts")
        user = await self.get_user_input()
        if not user:
            return
            
        print("\nPost types:")
        print("1. Timeline posts")
        print("2. Archived posts")
        print("3. Private archived posts")
        
        choice = input("Select post type (1-3): ").strip()
        label = "main" if choice == "1" else "archived" if choice == "2" else "private_archived"
        logger.debug(f"Post type selected: {label}")
        
        limit = int(input("How many posts to fetch? (default 20): ").strip() or "20")
        logger.debug(f"Fetch limit: {limit}")
        
        print(f"\nFetching {label} posts...")
        logger.info(f"Fetching {label} posts for user {user.username} (limit: {limit})")
        
        posts = await user.get_posts(label=label, limit=limit)
        logger.info(f"✓ Retrieved {len(posts)} posts")
        
        print(f"\n✓ Found {len(posts)} posts")
        for i, post in enumerate(posts[:10], 1):
            logger.debug(f"Post {i}: ID={post.id}, Price={post.price}, Media={len(getattr(post, 'media', []))}")
            print(f"\n--- Post {i} ---")
            print(f"ID: {post.id}")
            print(f"Text: {post.text[:100]}..." if post.text and len(post.text) > 100 else f"Text: {post.text}")
            print(f"Price: ${post.price/100 if post.price else 0}")
            print(f"Date: {post.created_at}")
            print(f"Likes: {getattr(post, 'likes_count', 0)}")
            print(f"Comments: {getattr(post, 'comments_count', 0)}")
            print(f"Media: {getattr(post, 'media_count', len(getattr(post, 'media', [])))}")
    
    async def test_get_messages(self):
        """Test getting messages"""
        user = await self.get_user_input()
        if not user:
            return
            
        limit = int(input("How many messages to fetch? (default 20): ").strip() or "20")
        
        print(f"\nFetching messages...")
        messages = await user.get_messages(limit=limit)
        
        print(f"\n✓ Found {len(messages)} messages")
        for i, msg in enumerate(messages[:10], 1):
            print(f"\n--- Message {i} ---")
            print(f"ID: {msg.id}")
            print(f"From: {msg.get_author().username}")
            print(f"Text: {msg.text[:100]}..." if msg.text and len(msg.text) > 100 else f"Text: {msg.text}")
            print(f"Price: ${msg.price/100 if msg.price else 0}")
            print(f"Date: {msg.created_at}")
            print(f"Is Tip: {msg.isTip}")
            print(f"Media Count: {msg.media_count or 0}")
    
    async def test_get_stories(self):
        """Test getting stories"""
        user = await self.get_user_input()
        if not user:
            return
            
        print("\nFetching stories...")
        stories = await user.get_stories()
        
        print(f"\n✓ Found {len(stories)} stories")
        for i, story in enumerate(stories, 1):
            print(f"\n--- Story {i} ---")
            print(f"ID: {story.id}")
            print(f"Date: {story.created_at}")
            print(f"Media Count: {getattr(story, 'media_count', len(getattr(story, 'media', [])))}")
            print(f"Can Like: {getattr(story, 'can_like', 'N/A')}")
    
    async def test_get_highlights(self):
        """Test getting highlights"""
        user = await self.get_user_input()
        if not user:
            return
            
        print("\nFetching highlights...")
        highlights = await user.get_highlights()
        
        print(f"\n✓ Found {len(highlights)} highlights")
        for i, highlight in enumerate(highlights, 1):
            print(f"\n--- Highlight {i} ---")
            print(f"ID: {highlight['id']}")
            print(f"Title: {highlight.get('title', 'Untitled')}")
            print(f"Stories Count: {highlight.get('storiesCount', 0)}")
    
    async def test_search_messages(self):
        """Test searching messages"""
        user = await self.get_user_input()
        if not user:
            return
            
        search_text = input("Enter search text: ").strip()
        if not search_text:
            return
            
        print(f"\nSearching messages for '{search_text}'...")
        results = await user.search_messages(text=search_text)
        
        print(f"\n✓ Found {len(results.get('list', []))} messages")
        for msg in results.get('list', [])[:10]:
            print(f"\nID: {msg['id']}")
            print(f"Text: {msg['text'][:100]}...")
    
    async def test_get_subscriptions(self):
        """Test getting subscriptions"""
        print("\nSubscription types:")
        print("1. Active subscriptions")
        print("2. Expired subscriptions")
        print("3. All subscriptions")
        
        choice = input("Select type (1-3): ").strip()
        sub_type = "active" if choice == "1" else "expired" if choice == "2" else "all"
        
        limit = int(input("How many to fetch? (default 20): ").strip() or "20")
        
        print(f"\nFetching {sub_type} subscriptions...")
        subs = await self.authed.get_subscriptions(limit=limit, sub_type=sub_type)
        
        print(f"\n✓ Found {len(subs)} subscriptions")
        for i, sub in enumerate(subs[:10], 1):
            print(f"\n--- Subscription {i} ---")
            print(f"Username: {sub.user.username}")
            print(f"Name: {sub.user.name}")
            print(f"Price: ${sub.get_price()}")
            print(f"Status: {'Active' if sub.is_active() else 'Expired'}")
            print(f"Expires: {sub.resolve_expires_at()}")
    
    async def test_get_chats(self):
        """Test getting chats"""
        limit = int(input("How many chats to fetch? (default 20): ").strip() or "20")
        
        print("\nFetching chats...")
        chats = await self.authed.get_chats(limit=limit)
        
        print(f"\n✓ Found {len(chats)} chats")
        for i, chat in enumerate(chats[:10], 1):
            print(f"\n--- Chat {i} ---")
            print(f"Username: {chat.get_username()}")
            print(f"Last Message: {chat.last_message.get('text', 'N/A') if chat.last_message else 'N/A'}")
    
    async def test_get_lists(self):
        """Test getting lists"""
        print("\nFetching lists...")
        lists = await self.authed.get_lists()
        
        print(f"\n✓ Found {len(lists)} lists")
        for i, lst in enumerate(lists, 1):
            print(f"\n--- List {i} ---")
            print(f"ID: {lst.get('id')}")
            print(f"Name: {lst.get('name')}")
            print(f"Users Count: {lst.get('usersCount', 0)}")
    
    async def test_get_transactions(self):
        """Test getting transactions"""
        print("\nFetching transactions...")
        transactions = await self.authed.get_transactions()
        
        print(f"\n✓ Found {len(transactions)} transactions")
        for i, trans in enumerate(transactions[:10], 1):
            print(f"\n--- Transaction {i} ---")
            print(f"Amount: ${trans.get('amount', 0)}")
            print(f"Type: {trans.get('type')}")
            print(f"Description: {trans.get('description')}")
    
    async def test_like_content(self):
        """Test liking content"""
        print("\nContent types:")
        print("1. Post")
        print("2. Message")
        print("3. Story")
        
        choice = input("Select content type (1-3): ").strip()
        category = "posts" if choice == "1" else "messages" if choice == "2" else "stories"
        
        user = await self.get_user_input()
        if not user:
            return
            
        content_id = input(f"Enter {category[:-1]} ID to like: ").strip()
        if not content_id:
            return
            
        action = input("Like (L) or Unlike (U)? ").strip().upper()
        
        if action == "L":
            result = await user.like(category=category, identifier=content_id)
            print("✓ Liked successfully" if result else "❌ Like failed")
        else:
            result = await user.unlike(category=category, identifier=content_id)
            print("✓ Unliked successfully" if result else "❌ Unlike failed")
    
    async def test_send_message(self):
        """Test sending a message"""
        logger.info("Testing: Send Message")
        user = await self.get_user_input("Enter username to send message to: ")
        if not user:
            return
            
        print("\nMessage options:")
        print("1. Send free text message")
        print("2. Send paid message")
        print("3. Send message with locked text")
        
        msg_type = input("Select message type (1-3): ").strip()
        
        message_text = input("Enter message text: ").strip()
        if not message_text:
            logger.error("Message text is required")
            return
            
        price = 0
        locked_text = False
        
        if msg_type == "2":
            price_input = input("Enter price in dollars (e.g., 5.99): ").strip()
            try:
                price = int(float(price_input) * 100)  # Convert to cents
                logger.debug(f"Price set to {price} cents (${price/100:.2f})")
            except ValueError:
                logger.error("Invalid price format")
                return
        elif msg_type == "3":
            locked_text = True
            logger.debug("Message will have locked text")
            
        print(f"\nSending {'paid' if price > 0 else 'free'} message to {user.username}...")
        logger.info(f"Sending message: text='{message_text[:50]}...', price={price}, locked={locked_text}")
        
        try:
            result = await user.send_message(
                text=message_text,
                price=price,
                locked_text=locked_text
            )
            
            if result:
                logger.info(f"✓ Message sent successfully! ID: {result.id}")
                print(f"\n✓ Message sent successfully!")
                print(f"Message ID: {result.id}")
                print(f"Text: {result.text}")
                print(f"Price: ${result.price/100:.2f}" if result.price else "Price: Free")
                print(f"Created: {result.created_at}")
            else:
                logger.error("Failed to send message - no result returned")
                print("❌ Failed to send message")
                
        except Exception as e:
            logger.error(f"Error sending message: {type(e).__name__}: {str(e)}")
            print(f"❌ Error: {str(e)}")
    
    async def run(self):
        """Main run loop"""
        logger.info("=" * 60)
        logger.info("OnlyFans API Function Tester Started")
        logger.info(f"Log file: {log_file_path}")
        logger.info("=" * 60)
        
        if not await self.initialize():
            logger.critical("Failed to initialize API")
            return
            
        while True:
            self.display_menu()
            choice = input("\nSelect function to test (0 to exit): ").strip()
            logger.debug(f"Menu selection: {choice}")
            
            try:
                if choice == "0":
                    logger.info("User selected exit")
                    break
                elif choice == "1":
                    self.test_count += 1
                    await self.test_get_user_info()
                elif choice == "2":
                    await self.test_get_posts()
                elif choice == "3":
                    await self.test_get_messages()
                elif choice == "4":
                    await self.test_get_stories()
                elif choice == "5":
                    await self.test_get_highlights()
                elif choice == "6":
                    await self.test_search_messages()
                elif choice == "7":
                    user = await self.get_user_input()
                    if user:
                        mass_msgs = await user.get_mass_messages()
                        print(f"\n✓ Found {len(mass_msgs)} mass messages")
                elif choice == "8":
                    await self.test_get_subscriptions()
                elif choice == "9":
                    user = await self.get_user_input()
                    if user:
                        print(f"\nSubscription price: ${user.subscription_price()}")
                elif choice == "10":
                    paid = await self.authed.get_paid_content()
                    print(f"\n✓ Found {len(paid)} paid content items")
                elif choice == "11":
                    user = await self.get_user_input()
                    if user:
                        post_id = input("Enter post ID: ").strip()
                        post = await user.get_post(post_id)
                        if post:
                            comments = await post.get_comments()
                            print(f"\n✓ Found {len(comments)} comments")
                elif choice == "12":
                    await self.test_get_chats()
                elif choice == "13":
                    vault_lists = await self.authed.get_vault_lists()
                    print(f"\n✓ Found {len(vault_lists)} vault lists")
                elif choice == "14":
                    await self.test_like_content()
                elif choice == "15":
                    user = await self.get_user_input()
                    if user:
                        post_id = input("Enter post ID to favorite: ").strip()
                        post = await user.get_post(post_id)
                        if post:
                            result = await post.favorite()
                            print("✓ Favorited successfully" if result else "❌ Favorite failed")
                elif choice == "16":
                    user = await self.get_user_input()
                    if user:
                        action = input("Block (B) or Unblock (U)? ").strip().upper()
                        if action == "B":
                            result = await user.block()
                            print("✓ Blocked successfully" if result else "❌ Block failed")
                        else:
                            result = await user.unblock()
                            print("✓ Unblocked successfully" if result else "❌ Unblock failed")
                elif choice == "17":
                    self.test_count += 1
                    await self.test_send_message()
                elif choice == "18":
                    await self.test_get_lists()
                elif choice == "19":
                    await self.test_get_transactions()
                elif choice == "20":
                    issues = await self.authed.get_login_issues()
                    print(f"\nLogin issues: {issues}")
                elif choice == "21":
                    blacklist = await self.authed.get_blacklist()
                    print(f"\n✓ Found {len(blacklist)} blacklisted users")
                elif choice == "22":
                    user = await self.get_user_input()
                    if user:
                        post_id = input("Enter post ID: ").strip()
                        post = await user.get_post(post_id)
                        if post:
                            print(f"\n✓ Post found: {post.text[:100]}...")
                elif choice == "23":
                    user = await self.get_user_input()
                    if user:
                        msg_id = input("Enter message ID: ").strip()
                        msg = await user.get_message_by_id(user.id, msg_id)
                        if msg:
                            print(f"\n✓ Message found: {msg.text[:100]}...")
                elif choice == "24":
                    user = await self.get_user_input()
                    if user:
                        socials = await user.get_socials()
                        print(f"\nSocial links: {socials}")
                elif choice == "25":
                    user = await self.get_user_input()
                    if user:
                        promos = await user.get_promotions()
                        print(f"\n✓ Found {len(promos)} active promotions")
                else:
                    print("Invalid choice!")
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in menu option {choice}: {type(e).__name__}: {str(e)}")
                logger.exception("Full error traceback:")
                print(f"\n❌ Error occurred: {type(e).__name__}: {str(e)}")
                print("Check the log file for details")
            
            input("\nPress Enter to continue...")
        
        # Log session summary
        logger.info("=" * 60)
        logger.info("Session Summary")
        logger.info(f"Tests run: {self.test_count}")
        logger.info(f"Errors encountered: {self.error_count}")
        logger.info("=" * 60)
        
        logger.info("Closing API connections...")
        await self.api.close_pools()
        logger.info("API connections closed")
        logger.info("OnlyFans API Function Tester finished")
        logger.info(f"Session log saved to: {log_file_path}")
        
        print("\n" + "=" * 60)
        print("Session Summary")
        print(f"Tests run: {self.test_count}")
        print(f"Errors encountered: {self.error_count}")
        print("=" * 60)
        print("\nGoodbye!")
        print(f"Session log saved to: {log_file_path}")


if __name__ == "__main__":
    print("OnlyFans API Function Tester")
    print("This tool lets you test all available API functions interactively")
    print()
    
    tester = APIFunctionTester()
    asyncio.run(tester.run())