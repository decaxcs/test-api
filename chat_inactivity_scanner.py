#!/usr/bin/env python3
"""
Chat Inactivity Scanner for OnlyFans
Analyzes user chat activity to identify inactive users for re-engagement campaigns
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatInactivityScanner:
    """Analyzes chat activity to identify inactive users"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.current_date = datetime.now(timezone.utc)
        
    def calculate_days_inactive(self, last_message_date: datetime) -> int:
        """Calculate days since last message"""
        if not last_message_date:
            return -1  # Never messaged
        
        # Handle timezone-aware vs timezone-naive datetimes
        current_date = self.current_date
        
        # If last_message_date has timezone info and current_date doesn't
        if last_message_date.tzinfo is not None and current_date.tzinfo is None:
            # Make current_date timezone-aware (UTC)
            current_date = current_date.replace(tzinfo=timezone.utc)
        # If current_date has timezone info and last_message_date doesn't
        elif current_date.tzinfo is not None and last_message_date.tzinfo is None:
            # Make last_message_date timezone-aware (UTC)
            last_message_date = last_message_date.replace(tzinfo=timezone.utc)
        
        delta = current_date - last_message_date
        return delta.days
    
    async def analyze_chat_activity(self, chat, limit_messages: int = 10) -> Dict[str, Any]:
        """Analyze a single chat for activity patterns"""
        try:
            user = chat.user
            chat_data = {
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "avatar": getattr(user, 'avatar', None),
                "is_subscribed": False,  # Will check later
                "last_message_date": None,
                "last_message_from_them": None,
                "last_message_from_me": None,
                "days_inactive": -1,
                "total_messages_checked": 0,
                "their_message_count": 0,
                "my_message_count": 0,
                "has_purchased_content": False,
                "activity_status": "never_messaged"
            }
            
            # Get recent messages to analyze activity
            try:
                messages = await user.get_messages(limit=limit_messages)
                
                if messages:
                    chat_data["total_messages_checked"] = len(messages)
                    
                    # Analyze messages
                    for message in messages:
                        # Get message date
                        if hasattr(message, 'created_at') and message.created_at:
                            msg_date = message.created_at
                            
                            # Update last message date (most recent message)
                            if not chat_data["last_message_date"]:
                                chat_data["last_message_date"] = msg_date
                            
                            # Check who sent the message
                            if hasattr(message, 'author') and message.author:
                                if message.author.id == user.id:
                                    # Message from them
                                    chat_data["their_message_count"] += 1
                                    if not chat_data["last_message_from_them"]:
                                        chat_data["last_message_from_them"] = msg_date
                                else:
                                    # Message from me
                                    chat_data["my_message_count"] += 1
                                    if not chat_data["last_message_from_me"]:
                                        chat_data["last_message_from_me"] = msg_date
                            
                            # Check for purchases
                            if hasattr(message, 'price') and message.price and message.price > 0:
                                chat_data["has_purchased_content"] = True
                    
                    # Calculate inactivity
                    if chat_data["last_message_date"]:
                        chat_data["days_inactive"] = self.calculate_days_inactive(chat_data["last_message_date"])
                        
                        # Determine activity status
                        days = chat_data["days_inactive"]
                        if days <= 7:
                            chat_data["activity_status"] = "active"
                        elif days <= 30:
                            chat_data["activity_status"] = "inactive_recent"
                        elif days <= 60:
                            chat_data["activity_status"] = "inactive_moderate"
                        elif days <= 180:
                            chat_data["activity_status"] = "inactive_long"
                        else:
                            chat_data["activity_status"] = "inactive_very_long"
                    
                    # Add conversation metrics
                    if chat_data["their_message_count"] > 0:
                        chat_data["engagement_ratio"] = chat_data["my_message_count"] / chat_data["their_message_count"]
                    else:
                        chat_data["engagement_ratio"] = 0
                        
            except Exception as e:
                logger.error(f"Error getting messages for {user.username}: {e}")
                chat_data["error"] = str(e)
            
            return chat_data
            
        except Exception as e:
            logger.error(f"Error analyzing chat: {e}")
            return None
    
    async def scan_all_chats(self, limit: int = 200, check_subscriptions: bool = True) -> Dict[str, Any]:
        """Scan all chats and categorize by activity level"""
        logger.info("Starting chat inactivity scan...")
        
        results = {
            "scan_date": self.current_date.isoformat(),
            "categories": {
                "active": [],  # Active in last 7 days
                "inactive_recent": [],  # 8-30 days
                "inactive_moderate": [],  # 31-60 days
                "inactive_long": [],  # 61-180 days
                "inactive_very_long": [],  # 180+ days
                "never_messaged": []  # No messages ever
            },
            "statistics": {
                "total_chats": 0,
                "active_count": 0,
                "inactive_count": 0,
                "never_messaged_count": 0,
                "with_purchases": 0,
                "subscribed_inactive": 0,
                "errors": 0
            },
            "recommendations": []
        }
        
        try:
            # Get all chats
            logger.info(f"Fetching up to {limit} chats...")
            chats = await self.api.get_chats(limit=limit, offset=0)
            results["statistics"]["total_chats"] = len(chats)
            
            # Get current subscriptions if requested
            subscribed_users = set()
            if check_subscriptions:
                logger.info("Fetching active subscriptions...")
                try:
                    subscriptions = await self.api.get_subscriptions(limit=200)
                    for sub in subscriptions:
                        if hasattr(sub, 'user') and sub.user:
                            subscribed_users.add(sub.user.username)
                except Exception as e:
                    logger.error(f"Error fetching subscriptions: {e}")
            
            # Analyze each chat
            logger.info(f"Analyzing {len(chats)} chats...")
            for i, chat in enumerate(chats):
                if i % 10 == 0:
                    logger.info(f"Processing chat {i+1}/{len(chats)}...")
                
                try:
                    chat_analysis = await self.analyze_chat_activity(chat)
                    
                    if chat_analysis:
                        # Check subscription status
                        if chat_analysis["username"] in subscribed_users:
                            chat_analysis["is_subscribed"] = True
                            
                        # Categorize by activity status
                        status = chat_analysis["activity_status"]
                        results["categories"][status].append(chat_analysis)
                        
                        # Update statistics
                        if status == "active":
                            results["statistics"]["active_count"] += 1
                        elif status == "never_messaged":
                            results["statistics"]["never_messaged_count"] += 1
                        else:
                            results["statistics"]["inactive_count"] += 1
                            if chat_analysis["is_subscribed"]:
                                results["statistics"]["subscribed_inactive"] += 1
                        
                        if chat_analysis["has_purchased_content"]:
                            results["statistics"]["with_purchases"] += 1
                    else:
                        results["statistics"]["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing chat: {e}")
                    results["statistics"]["errors"] += 1
            
            # Sort categories by days inactive
            for category in results["categories"]:
                if category != "never_messaged":
                    results["categories"][category].sort(
                        key=lambda x: x["days_inactive"], 
                        reverse=True
                    )
            
            # Generate recommendations
            results["recommendations"] = self.generate_recommendations(results)
            
            logger.info("Chat inactivity scan completed!")
            return results
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            raise
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on scan results"""
        recommendations = []
        stats = results["statistics"]
        
        # Calculate percentages
        if stats["total_chats"] > 0:
            inactive_percent = (stats["inactive_count"] / stats["total_chats"]) * 100
            never_messaged_percent = (stats["never_messaged_count"] / stats["total_chats"]) * 100
            
            if inactive_percent > 50:
                recommendations.append(
                    f"⚠️ High inactivity rate: {inactive_percent:.1f}% of chats are inactive. "
                    "Consider a re-engagement campaign."
                )
            
            if never_messaged_percent > 30:
                recommendations.append(
                    f"💬 {never_messaged_percent:.1f}% of users have never messaged. "
                    "Consider sending welcome messages to new subscribers."
                )
            
            if stats["subscribed_inactive"] > 10:
                recommendations.append(
                    f"💎 {stats['subscribed_inactive']} active subscribers are not engaging. "
                    "These are high-value targets for re-engagement."
                )
            
            # Specific recommendations by category
            recent_inactive = len(results["categories"]["inactive_recent"])
            if recent_inactive > 20:
                recommendations.append(
                    f"🔄 {recent_inactive} users became inactive in the last month. "
                    "Quick action could re-engage them."
                )
            
            with_purchases = stats["with_purchases"]
            if with_purchases > 0:
                purchase_inactive = sum(
                    1 for cat in ["inactive_moderate", "inactive_long", "inactive_very_long"]
                    for user in results["categories"][cat]
                    if user["has_purchased_content"]
                )
                if purchase_inactive > 5:
                    recommendations.append(
                        f"💰 {purchase_inactive} users who made purchases are now inactive. "
                        "These are prime candidates for win-back offers."
                    )
        
        if not recommendations:
            recommendations.append("✅ Chat activity looks healthy overall!")
        
        return recommendations
    
    def export_results(self, results: Dict[str, Any], filename: str = "inactivity_report.json"):
        """Export results to JSON file"""
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results exported to {output_path}")
        return output_path


async def main():
    """Main function to run the inactivity scanner"""
    try:
        # Load authentication
        auth_path = Path("auth.json")
        if not auth_path.exists():
            logger.error("auth.json not found!")
            return
        
        auth_data = json.loads(auth_path.read_text())
        
        # Initialize API
        config = UltimaScraperAPIConfig()
        api = OnlyFansAPI(config)
        
        # Authenticate
        logger.info("Authenticating...")
        authed = await api.login(auth_data["auth"])
        
        if not authed or not authed.is_authed():
            logger.error("Authentication failed!")
            return
        
        logger.info(f"Authenticated as: {authed.username}")
        
        # Create scanner instance
        scanner = ChatInactivityScanner(authed)
        
        # Run the scan
        results = await scanner.scan_all_chats(
            limit=200,  # Adjust based on your needs
            check_subscriptions=True
        )
        
        # Print summary
        print("\n" + "="*60)
        print("CHAT INACTIVITY SCAN RESULTS")
        print("="*60)
        
        stats = results["statistics"]
        print(f"\nTotal Chats Analyzed: {stats['total_chats']}")
        print(f"Active Chats (≤7 days): {stats['active_count']}")
        print(f"Inactive Chats: {stats['inactive_count']}")
        print(f"Never Messaged: {stats['never_messaged_count']}")
        print(f"With Purchases: {stats['with_purchases']}")
        print(f"Subscribed but Inactive: {stats['subscribed_inactive']}")
        
        print("\n" + "-"*40)
        print("BREAKDOWN BY INACTIVITY PERIOD:")
        print("-"*40)
        
        for category, users in results["categories"].items():
            if users:
                print(f"\n{category.replace('_', ' ').title()}: {len(users)} users")
                # Show top 5 from each category
                for user in users[:5]:
                    days = user['days_inactive']
                    status = "📱" if user['is_subscribed'] else "👤"
                    purchase = "💰" if user['has_purchased_content'] else ""
                    print(f"  {status} @{user['username']} - {days} days inactive {purchase}")
                if len(users) > 5:
                    print(f"  ... and {len(users) - 5} more")
        
        print("\n" + "-"*40)
        print("RECOMMENDATIONS:")
        print("-"*40)
        for rec in results["recommendations"]:
            print(f"\n{rec}")
        
        # Export results
        export_path = scanner.export_results(results)
        print(f"\n✅ Full report exported to: {export_path}")
        
        # Example: Get users for targeted campaign
        print("\n" + "="*60)
        print("SUGGESTED TARGETS FOR RE-ENGAGEMENT:")
        print("="*60)
        
        # High-value inactive users (subscribed or made purchases)
        high_value_targets = []
        for category in ["inactive_recent", "inactive_moderate"]:
            for user in results["categories"][category]:
                if user["is_subscribed"] or user["has_purchased_content"]:
                    high_value_targets.append(user)
        
        if high_value_targets:
            print(f"\nFound {len(high_value_targets)} high-value inactive users:")
            for user in high_value_targets[:10]:
                print(f"  @{user['username']} - {user['days_inactive']} days inactive "
                      f"({'Subscribed' if user['is_subscribed'] else 'Purchased content'})")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())