#!/usr/bin/env python3
"""
All Fans Comprehensive Analyzer for OnlyFans Creators
Analyzes ALL fans with detailed activity, spending, and engagement metrics
"""

import asyncio
import json
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
import time

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AllFansComprehensiveAnalyzer:
    """Analyzes all fans comprehensively"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.current_date = datetime.now(timezone.utc)
        self.creator_id = api_instance.id
        self.creator_username = api_instance.username
        self.start_time = time.time()
    
    def calculate_days_between(self, date1: datetime, date2: datetime = None) -> int:
        """Calculate days between two dates"""
        if not date1:
            return -1
        
        if not date2:
            date2 = self.current_date
        
        # Handle timezone
        if date1.tzinfo is None:
            date1 = date1.replace(tzinfo=timezone.utc)
        if date2.tzinfo is None:
            date2 = date2.replace(tzinfo=timezone.utc)
        
        delta = date2 - date1
        return delta.days
    
    async def analyze_fan_quick(self, chat, message_limit: int = 100) -> Dict[str, Any]:
        """Quick analysis of a single fan for batch processing"""
        try:
            user = chat.user
            
            # Initialize fan data
            fan_data = {
                # Basic info
                "fan_id": user.id,
                "username": user.username,
                "name": user.name,
                
                # Activity metrics
                "first_interaction": None,
                "last_interaction": None,
                "days_since_last_interaction": -1,
                "total_messages": 0,
                "messages_from_fan": 0,
                "messages_from_creator": 0,
                "activity_status": "unknown",
                
                # Spending metrics
                "total_spent": 0,
                "ppv_purchases": 0,
                "ppv_total": 0,
                "tips_sent": 0,
                "tips_total": 0,
                "last_purchase_date": None,
                "days_since_last_purchase": -1,
                "spending_status": "never",
                
                # Engagement metrics
                "response_rate": 0,
                "initiates_conversations": False,
                "engagement_score": 0,
                
                # Content metrics
                "ppv_sent": 0,
                "ppv_opened": 0,
                "ppv_unopened": 0,
                "ppv_open_rate": 0,
                
                # Categories
                "is_vip": False,
                "is_whale": False,
                "is_active_spender": False,
                "is_dormant": False,
                "is_engaged": False,
                "needs_attention": False
            }
            
            # Get messages
            messages = await user.get_messages(limit=message_limit)
            
            if not messages:
                fan_data["activity_status"] = "no_interaction"
                return fan_data
            
            # Analyze messages
            purchases = []
            conversation_starts = 0
            last_creator_msg_time = None
            
            for i, message in enumerate(messages):
                msg_time = message.created_at if hasattr(message, 'created_at') else None
                if not msg_time:
                    continue
                
                # Ensure timezone aware
                if msg_time.tzinfo is None:
                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                
                # Track first and last interaction
                if not fan_data["first_interaction"] or msg_time < fan_data["first_interaction"]:
                    fan_data["first_interaction"] = msg_time
                if not fan_data["last_interaction"] or msg_time > fan_data["last_interaction"]:
                    fan_data["last_interaction"] = msg_time
                
                # Determine author
                author_id = None
                if hasattr(message, 'author') and hasattr(message.author, 'id'):
                    author_id = message.author.id
                elif hasattr(message, 'fromUser') and hasattr(message.fromUser, 'id'):
                    author_id = message.fromUser.id
                
                is_from_fan = (author_id == user.id)
                
                # Count messages
                fan_data["total_messages"] += 1
                if is_from_fan:
                    fan_data["messages_from_fan"] += 1
                    # Check if fan initiated after creator's message
                    if last_creator_msg_time and (msg_time - last_creator_msg_time).total_seconds() > 3600:
                        conversation_starts += 1
                else:
                    fan_data["messages_from_creator"] += 1
                    last_creator_msg_time = msg_time
                
                # Check for purchases
                price = getattr(message, 'price', 0) or 0
                if price > 0:
                    is_tip = getattr(message, 'isTip', False)
                    is_opened = getattr(message, 'isOpened', True)
                    
                    # Track all PPV sent
                    if not is_tip and not is_from_fan:
                        fan_data["ppv_sent"] += 1
                        if is_opened:
                            fan_data["ppv_opened"] += 1
                        else:
                            fan_data["ppv_unopened"] += 1
                    
                    # Track purchases
                    is_purchase = False
                    if is_tip and is_from_fan:
                        is_purchase = True
                        fan_data["tips_sent"] += 1
                        fan_data["tips_total"] += price
                    elif not is_tip and not is_from_fan and is_opened:
                        is_purchase = True
                        fan_data["ppv_purchases"] += 1
                        fan_data["ppv_total"] += price
                    
                    if is_purchase:
                        fan_data["total_spent"] += price
                        purchases.append({
                            "date": msg_time,
                            "amount": price
                        })
                        
                        if not fan_data["last_purchase_date"] or msg_time > fan_data["last_purchase_date"]:
                            fan_data["last_purchase_date"] = msg_time
            
            # Calculate metrics
            if fan_data["last_interaction"]:
                fan_data["days_since_last_interaction"] = self.calculate_days_between(fan_data["last_interaction"])
            
            if fan_data["last_purchase_date"]:
                fan_data["days_since_last_purchase"] = self.calculate_days_between(fan_data["last_purchase_date"])
            
            # Activity status
            if fan_data["days_since_last_interaction"] <= 7:
                fan_data["activity_status"] = "active"
            elif fan_data["days_since_last_interaction"] <= 30:
                fan_data["activity_status"] = "semi_active"
            elif fan_data["days_since_last_interaction"] <= 90:
                fan_data["activity_status"] = "inactive"
            else:
                fan_data["activity_status"] = "dormant"
                fan_data["is_dormant"] = True
            
            # Spending status
            if fan_data["total_spent"] > 0:
                if fan_data["days_since_last_purchase"] <= 30:
                    fan_data["spending_status"] = "active_spender"
                    fan_data["is_active_spender"] = True
                elif fan_data["days_since_last_purchase"] <= 90:
                    fan_data["spending_status"] = "moderate_spender"
                else:
                    fan_data["spending_status"] = "dormant_spender"
            
            # Response rate
            if fan_data["messages_from_creator"] > 0:
                fan_data["response_rate"] = round(
                    fan_data["messages_from_fan"] / fan_data["messages_from_creator"] * 100, 1
                )
            
            # PPV open rate
            if fan_data["ppv_sent"] > 0:
                fan_data["ppv_open_rate"] = round(
                    fan_data["ppv_opened"] / fan_data["ppv_sent"] * 100, 1
                )
            
            # Initiates conversations
            fan_data["initiates_conversations"] = conversation_starts > 2
            
            # Categorize
            total_spent_dollars = fan_data["total_spent"] / 100
            if total_spent_dollars >= 500:
                fan_data["is_vip"] = True
                fan_data["is_whale"] = True
            elif total_spent_dollars >= 200:
                fan_data["is_whale"] = True
            
            # Engagement score (simplified)
            score = 0
            if fan_data["response_rate"] >= 50: score += 25
            if fan_data["total_spent"] > 0: score += 25
            if fan_data["activity_status"] == "active": score += 25
            if fan_data["initiates_conversations"]: score += 25
            fan_data["engagement_score"] = score
            fan_data["is_engaged"] = score >= 50
            
            # Needs attention flags
            if fan_data["is_whale"] and fan_data["is_dormant"]:
                fan_data["needs_attention"] = True
            elif fan_data["is_whale"] and fan_data["spending_status"] != "active_spender":
                fan_data["needs_attention"] = True
            elif fan_data["engagement_score"] >= 75 and fan_data["total_spent"] == 0:
                fan_data["needs_attention"] = True
            
            return fan_data
            
        except Exception as e:
            logger.error(f"Error analyzing fan {chat.user.username}: {e}")
            return None
    
    async def analyze_all_fans(self, chat_limit: int = 200, message_limit: int = 100) -> Dict[str, Any]:
        """Analyze all fans comprehensively"""
        logger.info(f"Starting comprehensive analysis of all fans...")
        
        results = {
            "creator": {
                "username": self.creator_username,
                "id": self.creator_id
            },
            "analysis_date": self.current_date.isoformat(),
            "summary": {
                "total_fans": 0,
                "active_fans": 0,
                "total_revenue": 0,
                "active_spenders": 0,
                "dormant_fans": 0,
                "vip_count": 0,
                "whale_count": 0,
                "engaged_non_spenders": 0,
                "needs_attention_count": 0
            },
            "categories": {
                "vip_fans": [],
                "whales": [],
                "active_spenders": [],
                "dormant_high_value": [],
                "engaged_non_spenders": [],
                "needs_immediate_attention": [],
                "new_fans": [],
                "lost_fans": []
            },
            "insights": [],
            "all_fans_data": []
        }
        
        try:
            # Get all chats
            logger.info(f"Fetching up to {chat_limit} chats...")
            chats = await self.api.get_chats(limit=chat_limit, offset=0)
            results["summary"]["total_fans"] = len(chats)
            
            # Progress tracking
            analyzed = 0
            errors = 0
            
            # Analyze each fan
            logger.info(f"Analyzing {len(chats)} fans...")
            
            for i, chat in enumerate(chats):
                # Progress update every 10 fans
                if i % 10 == 0:
                    elapsed = time.time() - self.start_time
                    rate = (i + 1) / elapsed if elapsed > 0 else 0
                    eta = (len(chats) - i) / rate if rate > 0 else 0
                    logger.info(f"Progress: {i+1}/{len(chats)} fans ({(i+1)/len(chats)*100:.1f}%) - ETA: {eta/60:.1f} minutes")
                
                try:
                    fan_data = await self.analyze_fan_quick(chat, message_limit)
                    
                    if fan_data:
                        analyzed += 1
                        
                        # Add to all fans data
                        results["all_fans_data"].append(fan_data)
                        
                        # Update summary
                        if fan_data["activity_status"] == "active":
                            results["summary"]["active_fans"] += 1
                        
                        if fan_data["total_spent"] > 0:
                            results["summary"]["total_revenue"] += fan_data["total_spent"]
                        
                        if fan_data["is_active_spender"]:
                            results["summary"]["active_spenders"] += 1
                        
                        if fan_data["is_dormant"]:
                            results["summary"]["dormant_fans"] += 1
                        
                        if fan_data["is_vip"]:
                            results["summary"]["vip_count"] += 1
                        
                        if fan_data["is_whale"]:
                            results["summary"]["whale_count"] += 1
                        
                        if fan_data["is_engaged"] and fan_data["total_spent"] == 0:
                            results["summary"]["engaged_non_spenders"] += 1
                        
                        if fan_data["needs_attention"]:
                            results["summary"]["needs_attention_count"] += 1
                        
                        # Categorize fans
                        if fan_data["is_vip"]:
                            results["categories"]["vip_fans"].append(fan_data)
                        elif fan_data["is_whale"]:
                            results["categories"]["whales"].append(fan_data)
                        
                        if fan_data["is_active_spender"]:
                            results["categories"]["active_spenders"].append(fan_data)
                        
                        if fan_data["is_whale"] and fan_data["is_dormant"]:
                            results["categories"]["dormant_high_value"].append(fan_data)
                        
                        if fan_data["is_engaged"] and fan_data["total_spent"] == 0:
                            results["categories"]["engaged_non_spenders"].append(fan_data)
                        
                        if fan_data["needs_attention"]:
                            results["categories"]["needs_immediate_attention"].append(fan_data)
                        
                        # New fans (interacted within 30 days of first interaction)
                        if fan_data["first_interaction"] and fan_data["last_interaction"]:
                            days_active = self.calculate_days_between(
                                fan_data["first_interaction"],
                                fan_data["last_interaction"]
                            )
                            if days_active <= 30 and fan_data["days_since_last_interaction"] <= 30:
                                results["categories"]["new_fans"].append(fan_data)
                        
                        # Lost fans (were active spenders but now dormant)
                        if fan_data["total_spent"] > 5000 and fan_data["is_dormant"]:
                            results["categories"]["lost_fans"].append(fan_data)
                    else:
                        errors += 1
                        
                except Exception as e:
                    logger.error(f"Error processing fan: {e}")
                    errors += 1
                
                # Small delay to avoid rate limits
                if i % 50 == 49:
                    await asyncio.sleep(1)
            
            logger.info(f"Analysis complete! Analyzed {analyzed} fans with {errors} errors")
            
            # Sort categories by value/importance
            for category in ["vip_fans", "whales", "active_spenders", "dormant_high_value"]:
                results["categories"][category].sort(
                    key=lambda x: x["total_spent"],
                    reverse=True
                )
            
            results["categories"]["engaged_non_spenders"].sort(
                key=lambda x: x["engagement_score"],
                reverse=True
            )
            
            results["categories"]["needs_immediate_attention"].sort(
                key=lambda x: (x["total_spent"], x["engagement_score"]),
                reverse=True
            )
            
            # Generate insights
            results["insights"] = self.generate_insights(results)
            
            # Add execution time
            results["execution_time_seconds"] = round(time.time() - self.start_time, 2)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise
    
    def generate_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate insights from the analysis"""
        insights = []
        summary = results["summary"]
        
        # Revenue insights
        if summary["total_revenue"] > 0:
            avg_revenue_per_fan = summary["total_revenue"] / summary["total_fans"] if summary["total_fans"] > 0 else 0
            insights.append(f"💰 Total revenue from analyzed fans: ${summary['total_revenue']/100:.2f} (avg ${avg_revenue_per_fan/100:.2f} per fan)")
        
        # Activity insights
        if summary["total_fans"] > 0:
            active_percent = (summary["active_fans"] / summary["total_fans"]) * 100
            insights.append(f"📊 {active_percent:.1f}% of fans are currently active (messaged within 7 days)")
        
        # Spending insights
        if summary["whale_count"] > 0:
            whale_revenue = sum(f["total_spent"] for f in results["categories"]["whales"] + results["categories"]["vip_fans"])
            whale_percent = (whale_revenue / summary["total_revenue"] * 100) if summary["total_revenue"] > 0 else 0
            insights.append(f"🐋 {summary['whale_count']} whales generate ${whale_revenue/100:.2f} ({whale_percent:.1f}% of revenue)")
        
        # Opportunity insights
        if summary["engaged_non_spenders"] > 0:
            insights.append(f"🎯 {summary['engaged_non_spenders']} engaged fans haven't spent yet - prime conversion targets!")
        
        if len(results["categories"]["dormant_high_value"]) > 0:
            dormant_value = sum(f["total_spent"] for f in results["categories"]["dormant_high_value"])
            insights.append(f"⚠️ {len(results['categories']['dormant_high_value'])} high-value fans are dormant (${dormant_value/100:.2f} lifetime value)")
        
        # Attention needed
        if summary["needs_attention_count"] > 0:
            insights.append(f"🚨 {summary['needs_attention_count']} fans need immediate attention for retention/conversion")
        
        # New fans
        if len(results["categories"]["new_fans"]) > 0:
            new_fan_spenders = sum(1 for f in results["categories"]["new_fans"] if f["total_spent"] > 0)
            insights.append(f"🌟 {len(results['categories']['new_fans'])} new fans joined recently ({new_fan_spenders} are already spending)")
        
        return insights
    
    def export_results(self, results: Dict[str, Any], base_filename: str = "all_fans_analysis"):
        """Export results to JSON and CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export full JSON report
        json_filename = f"{base_filename}_{timestamp}.json"
        json_path = Path(json_filename)
        
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=serialize_dates)
        
        logger.info(f"Full report exported to {json_path}")
        
        # Export CSV for spreadsheet analysis
        csv_filename = f"{base_filename}_{timestamp}.csv"
        csv_path = Path(csv_filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if results["all_fans_data"]:
                # Define CSV columns
                fieldnames = [
                    'username', 'name', 'activity_status', 'days_since_last_interaction',
                    'total_messages', 'messages_from_fan', 'response_rate',
                    'total_spent_dollars', 'ppv_purchases', 'tips_sent',
                    'days_since_last_purchase', 'spending_status',
                    'ppv_open_rate', 'engagement_score',
                    'is_vip', 'is_whale', 'is_active_spender', 'needs_attention'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write fan data
                for fan in results["all_fans_data"]:
                    row = {
                        'username': fan['username'],
                        'name': fan['name'],
                        'activity_status': fan['activity_status'],
                        'days_since_last_interaction': fan['days_since_last_interaction'],
                        'total_messages': fan['total_messages'],
                        'messages_from_fan': fan['messages_from_fan'],
                        'response_rate': fan['response_rate'],
                        'total_spent_dollars': fan['total_spent'] / 100,
                        'ppv_purchases': fan['ppv_purchases'],
                        'tips_sent': fan['tips_sent'],
                        'days_since_last_purchase': fan['days_since_last_purchase'],
                        'spending_status': fan['spending_status'],
                        'ppv_open_rate': fan['ppv_open_rate'],
                        'engagement_score': fan['engagement_score'],
                        'is_vip': fan['is_vip'],
                        'is_whale': fan['is_whale'],
                        'is_active_spender': fan['is_active_spender'],
                        'needs_attention': fan['needs_attention']
                    }
                    writer.writerow(row)
        
        logger.info(f"CSV data exported to {csv_path}")
        
        # Export priority action list
        action_filename = f"{base_filename}_actions_{timestamp}.txt"
        action_path = Path(action_filename)
        
        with open(action_path, 'w', encoding='utf-8') as f:
            f.write("PRIORITY ACTION LIST\n")
            f.write("=" * 50 + "\n\n")
            
            # Immediate attention needed
            f.write("🚨 IMMEDIATE ATTENTION NEEDED:\n")
            f.write("-" * 30 + "\n")
            for fan in results["categories"]["needs_immediate_attention"][:20]:
                f.write(f"@{fan['username']} - ${fan['total_spent']/100:.2f} lifetime")
                if fan['is_dormant']:
                    f.write(f" - DORMANT {fan['days_since_last_interaction']} days")
                f.write("\n")
            
            f.write("\n\n💎 HIGH-VALUE DORMANT FANS:\n")
            f.write("-" * 30 + "\n")
            for fan in results["categories"]["dormant_high_value"][:20]:
                f.write(f"@{fan['username']} - ${fan['total_spent']/100:.2f} lifetime - Last seen {fan['days_since_last_interaction']} days ago\n")
            
            f.write("\n\n🎯 ENGAGED NON-SPENDERS TO CONVERT:\n")
            f.write("-" * 30 + "\n")
            for fan in results["categories"]["engaged_non_spenders"][:20]:
                f.write(f"@{fan['username']} - Score: {fan['engagement_score']}/100 - {fan['total_messages']} messages\n")
        
        logger.info(f"Action list exported to {action_path}")
        
        return json_path, csv_path, action_path


async def main():
    """Main function"""
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
        
        logger.info(f"Authenticated as creator: {authed.username}")
        
        # Create analyzer
        analyzer = AllFansComprehensiveAnalyzer(authed)
        
        # Run analysis
        results = await analyzer.analyze_all_fans(
            chat_limit=200,  # Analyze up to 200 fans
            message_limit=100  # Check last 100 messages per fan
        )
        
        # Print summary
        print("\n" + "="*70)
        print("📊 ALL FANS COMPREHENSIVE ANALYSIS")
        print("="*70)
        print(f"Creator: @{results['creator']['username']}")
        print(f"Analysis completed in: {results['execution_time_seconds']:.1f} seconds")
        
        summary = results["summary"]
        print(f"\n📈 SUMMARY:")
        print(f"  Total Fans: {summary['total_fans']}")
        print(f"  Active Fans: {summary['active_fans']} ({summary['active_fans']/summary['total_fans']*100:.1f}%)")
        print(f"  Total Revenue: ${summary['total_revenue']/100:.2f}")
        print(f"  Active Spenders: {summary['active_spenders']}")
        print(f"  VIPs: {summary['vip_count']}")
        print(f"  Whales: {summary['whale_count']}")
        print(f"  Needs Attention: {summary['needs_attention_count']}")
        
        # Top categories
        print(f"\n🏆 TOP VIPS:")
        for fan in results["categories"]["vip_fans"][:5]:
            print(f"  @{fan['username']} - ${fan['total_spent']/100:.2f} - {fan['activity_status']}")
        
        print(f"\n⚠️ NEEDS IMMEDIATE ATTENTION:")
        for fan in results["categories"]["needs_immediate_attention"][:10]:
            reason = "Dormant whale" if fan['is_dormant'] and fan['is_whale'] else "High potential"
            print(f"  @{fan['username']} - ${fan['total_spent']/100:.2f} - {reason}")
        
        print(f"\n🎯 TOP CONVERSION OPPORTUNITIES:")
        for fan in results["categories"]["engaged_non_spenders"][:5]:
            print(f"  @{fan['username']} - Score: {fan['engagement_score']}/100 - {fan['total_messages']} messages")
        
        # Insights
        print(f"\n💡 KEY INSIGHTS:")
        for insight in results["insights"]:
            print(f"  {insight}")
        
        # Export results
        json_path, csv_path, action_path = analyzer.export_results(results)
        
        print(f"\n✅ Reports exported:")
        print(f"  - Full JSON report: {json_path}")
        print(f"  - CSV for spreadsheets: {csv_path}")
        print(f"  - Priority action list: {action_path}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())