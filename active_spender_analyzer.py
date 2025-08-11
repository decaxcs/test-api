#!/usr/bin/env python3
"""
Active Spender Analyzer for OnlyFans
Analyzes spending patterns to identify high-value customers and spending trends
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActiveSpenderAnalyzer:
    """Analyzes spending patterns to identify valuable customers"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.current_date = datetime.now(timezone.utc)
    
    def calculate_days_ago(self, date: datetime) -> int:
        """Calculate days between date and now"""
        if not date:
            return -1
        
        # Handle timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        delta = self.current_date - date
        return delta.days
    
    async def analyze_user_spending(self, chat, message_limit: int = 100) -> Dict[str, Any]:
        """Analyze spending for a single user"""
        try:
            user = chat.user
            spending_data = {
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "avatar": getattr(user, 'avatar', None),
                "is_subscribed": False,
                "subscription_price": 0,
                "total_spent": 0,
                "ppv_purchases": 0,
                "tip_count": 0,
                "tip_total": 0,
                "last_purchase_date": None,
                "last_purchase_days_ago": -1,
                "first_purchase_date": None,
                "purchase_history": [],
                "spending_by_month": defaultdict(float),
                "average_purchase_value": 0,
                "highest_single_purchase": 0,
                "spending_frequency": "never",
                "customer_value_score": 0,
                "spending_trend": "unknown"
            }
            
            # Get messages to analyze purchases
            try:
                messages = await user.get_messages(limit=message_limit)
                
                purchases = []
                for message in messages:
                    # Check if this is a paid message (PPV or tip)
                    price = getattr(message, 'price', 0) or 0
                    if price > 0:
                        is_tip = getattr(message, 'isTip', False)
                        is_opened = getattr(message, 'isOpened', True)
                        
                        # Only count if it was actually purchased (opened)
                        if is_opened or is_tip:
                            purchase = {
                                "message_id": message.id,
                                "amount": price,
                                "amount_dollars": price / 100,
                                "type": "tip" if is_tip else "ppv",
                                "date": message.created_at if hasattr(message, 'created_at') else None,
                                "text_preview": (getattr(message, 'text', '')[:50] + "...") if getattr(message, 'text', '') else "",
                                "media_count": getattr(message, 'media_count', 0)
                            }
                            
                            purchases.append(purchase)
                            spending_data["total_spent"] += price
                            
                            if is_tip:
                                spending_data["tip_count"] += 1
                                spending_data["tip_total"] += price
                            else:
                                spending_data["ppv_purchases"] += 1
                            
                            # Track highest purchase
                            if price > spending_data["highest_single_purchase"]:
                                spending_data["highest_single_purchase"] = price
                            
                            # Track dates
                            if purchase["date"]:
                                if not spending_data["last_purchase_date"] or purchase["date"] > spending_data["last_purchase_date"]:
                                    spending_data["last_purchase_date"] = purchase["date"]
                                if not spending_data["first_purchase_date"] or purchase["date"] < spending_data["first_purchase_date"]:
                                    spending_data["first_purchase_date"] = purchase["date"]
                                
                                # Track by month
                                month_key = purchase["date"].strftime("%Y-%m")
                                spending_data["spending_by_month"][month_key] += price
                
                # Sort purchases by date (newest first)
                purchases.sort(key=lambda x: x["date"] if x["date"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                spending_data["purchase_history"] = purchases[:20]  # Keep last 20 purchases
                
                # Calculate metrics
                if purchases:
                    spending_data["average_purchase_value"] = spending_data["total_spent"] / len(purchases)
                    
                    # Calculate days since last purchase
                    if spending_data["last_purchase_date"]:
                        spending_data["last_purchase_days_ago"] = self.calculate_days_ago(spending_data["last_purchase_date"])
                    
                    # Determine spending frequency
                    if spending_data["last_purchase_days_ago"] >= 0:
                        if spending_data["last_purchase_days_ago"] <= 7:
                            spending_data["spending_frequency"] = "very_active"
                        elif spending_data["last_purchase_days_ago"] <= 30:
                            spending_data["spending_frequency"] = "active"
                        elif spending_data["last_purchase_days_ago"] <= 60:
                            spending_data["spending_frequency"] = "moderate"
                        elif spending_data["last_purchase_days_ago"] <= 180:
                            spending_data["spending_frequency"] = "inactive"
                        else:
                            spending_data["spending_frequency"] = "dormant"
                    
                    # Calculate spending trend (comparing recent vs older spending)
                    if len(spending_data["spending_by_month"]) >= 2:
                        months = sorted(spending_data["spending_by_month"].keys())
                        recent_months = months[-2:]  # Last 2 months
                        older_months = months[:-2] if len(months) > 2 else months[:1]
                        
                        recent_avg = sum(spending_data["spending_by_month"][m] for m in recent_months) / len(recent_months)
                        older_avg = sum(spending_data["spending_by_month"][m] for m in older_months) / len(older_months) if older_months else 0
                        
                        if older_avg > 0:
                            trend_ratio = recent_avg / older_avg
                            if trend_ratio > 1.5:
                                spending_data["spending_trend"] = "increasing"
                            elif trend_ratio < 0.5:
                                spending_data["spending_trend"] = "decreasing"
                            else:
                                spending_data["spending_trend"] = "stable"
                
                # Calculate customer value score (0-100)
                score = 0
                
                # Total spending factor (up to 40 points)
                if spending_data["total_spent"] > 0:
                    if spending_data["total_spent"] >= 50000:  # $500+
                        score += 40
                    elif spending_data["total_spent"] >= 20000:  # $200+
                        score += 30
                    elif spending_data["total_spent"] >= 10000:  # $100+
                        score += 20
                    elif spending_data["total_spent"] >= 5000:  # $50+
                        score += 10
                    else:
                        score += 5
                
                # Frequency factor (up to 30 points)
                frequency_scores = {
                    "very_active": 30,
                    "active": 20,
                    "moderate": 10,
                    "inactive": 5,
                    "dormant": 0
                }
                score += frequency_scores.get(spending_data["spending_frequency"], 0)
                
                # Purchase count factor (up to 20 points)
                total_purchases = spending_data["ppv_purchases"] + spending_data["tip_count"]
                if total_purchases >= 20:
                    score += 20
                elif total_purchases >= 10:
                    score += 15
                elif total_purchases >= 5:
                    score += 10
                elif total_purchases >= 1:
                    score += 5
                
                # Trend factor (up to 10 points)
                trend_scores = {
                    "increasing": 10,
                    "stable": 5,
                    "decreasing": 0
                }
                score += trend_scores.get(spending_data["spending_trend"], 0)
                
                spending_data["customer_value_score"] = min(score, 100)
                
                # Get paid content purchases
                try:
                    paid_content = await user.get_paid_contents()
                    for content in paid_content:
                        if hasattr(content, 'price') and content.price:
                            spending_data["total_spent"] += content.price
                            spending_data["ppv_purchases"] += 1
                except Exception as e:
                    logger.debug(f"Could not get paid content for {user.username}: {e}")
                
            except Exception as e:
                logger.error(f"Error analyzing messages for {user.username}: {e}")
                spending_data["error"] = str(e)
            
            # Convert spending_by_month to regular dict for JSON serialization
            spending_data["spending_by_month"] = dict(spending_data["spending_by_month"])
            
            return spending_data
            
        except Exception as e:
            logger.error(f"Error analyzing user spending: {e}")
            return None
    
    async def analyze_all_spenders(self, limit: int = 200, check_subscriptions: bool = True) -> Dict[str, Any]:
        """Analyze spending patterns across all chats"""
        logger.info("Starting spender analysis...")
        
        results = {
            "scan_date": self.current_date.isoformat(),
            "categories": {
                "whales": [],  # $200+ total spend
                "high_spenders": [],  # $100-200
                "moderate_spenders": [],  # $50-100
                "low_spenders": [],  # $10-50
                "micro_spenders": [],  # $1-10
                "non_spenders": []  # $0
            },
            "statistics": {
                "total_chats": 0,
                "total_spenders": 0,
                "total_revenue": 0,
                "total_ppv_purchases": 0,
                "total_tips": 0,
                "average_spend_per_user": 0,
                "average_spend_per_spender": 0,
                "highest_spender_amount": 0,
                "active_spenders_7d": 0,
                "active_spenders_30d": 0,
                "dormant_spenders": 0
            },
            "insights": [],
            "top_spenders": []
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
                            # Track subscription price
                            if hasattr(sub, 'subscribe_price'):
                                # Add subscription revenue estimation
                                pass
                except Exception as e:
                    logger.error(f"Error fetching subscriptions: {e}")
            
            # Analyze each chat
            all_spenders = []
            logger.info(f"Analyzing {len(chats)} chats for spending patterns...")
            
            for i, chat in enumerate(chats):
                if i % 10 == 0:
                    logger.info(f"Processing chat {i+1}/{len(chats)}...")
                
                try:
                    spending_analysis = await self.analyze_user_spending(chat)
                    
                    if spending_analysis:
                        # Check subscription status
                        if spending_analysis["username"] in subscribed_users:
                            spending_analysis["is_subscribed"] = True
                        
                        # Update statistics
                        if spending_analysis["total_spent"] > 0:
                            results["statistics"]["total_spenders"] += 1
                            results["statistics"]["total_revenue"] += spending_analysis["total_spent"]
                            results["statistics"]["total_ppv_purchases"] += spending_analysis["ppv_purchases"]
                            results["statistics"]["total_tips"] += spending_analysis["tip_count"]
                            
                            if spending_analysis["last_purchase_days_ago"] <= 7:
                                results["statistics"]["active_spenders_7d"] += 1
                            if spending_analysis["last_purchase_days_ago"] <= 30:
                                results["statistics"]["active_spenders_30d"] += 1
                            if spending_analysis["spending_frequency"] == "dormant":
                                results["statistics"]["dormant_spenders"] += 1
                            
                            if spending_analysis["total_spent"] > results["statistics"]["highest_spender_amount"]:
                                results["statistics"]["highest_spender_amount"] = spending_analysis["total_spent"]
                        
                        # Categorize spender
                        total_spent_dollars = spending_analysis["total_spent"] / 100
                        if total_spent_dollars >= 200:
                            results["categories"]["whales"].append(spending_analysis)
                        elif total_spent_dollars >= 100:
                            results["categories"]["high_spenders"].append(spending_analysis)
                        elif total_spent_dollars >= 50:
                            results["categories"]["moderate_spenders"].append(spending_analysis)
                        elif total_spent_dollars >= 10:
                            results["categories"]["low_spenders"].append(spending_analysis)
                        elif total_spent_dollars >= 1:
                            results["categories"]["micro_spenders"].append(spending_analysis)
                        else:
                            results["categories"]["non_spenders"].append(spending_analysis)
                        
                        all_spenders.append(spending_analysis)
                        
                except Exception as e:
                    logger.error(f"Error processing chat: {e}")
            
            # Calculate final statistics
            if results["statistics"]["total_chats"] > 0:
                results["statistics"]["average_spend_per_user"] = results["statistics"]["total_revenue"] / results["statistics"]["total_chats"]
            
            if results["statistics"]["total_spenders"] > 0:
                results["statistics"]["average_spend_per_spender"] = results["statistics"]["total_revenue"] / results["statistics"]["total_spenders"]
            
            # Sort categories by value score
            for category in results["categories"]:
                results["categories"][category].sort(
                    key=lambda x: x["customer_value_score"], 
                    reverse=True
                )
            
            # Get top 10 spenders
            all_spenders.sort(key=lambda x: x["total_spent"], reverse=True)
            results["top_spenders"] = all_spenders[:10]
            
            # Generate insights
            results["insights"] = self.generate_insights(results)
            
            logger.info("Spender analysis completed!")
            return results
            
        except Exception as e:
            logger.error(f"Error during spender analysis: {e}")
            raise
    
    def generate_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights based on spending analysis"""
        insights = []
        stats = results["statistics"]
        
        # Revenue concentration
        whale_count = len(results["categories"]["whales"])
        high_spender_count = len(results["categories"]["high_spenders"])
        total_spenders = stats["total_spenders"]
        
        if whale_count > 0:
            whale_revenue = sum(s["total_spent"] for s in results["categories"]["whales"])
            whale_percent = (whale_revenue / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0
            insights.append(
                f"🐋 {whale_count} whales ({whale_count/stats['total_chats']*100:.1f}% of users) "
                f"generate ${whale_revenue/100:.2f} ({whale_percent:.1f}% of revenue)"
            )
        
        # Spending activity
        if stats["total_spenders"] > 0:
            active_percent = (stats["active_spenders_30d"] / stats["total_spenders"] * 100)
            if active_percent < 50:
                insights.append(
                    f"⚠️ Only {stats['active_spenders_30d']} ({active_percent:.1f}%) of spenders "
                    f"made purchases in the last 30 days. Consider re-engagement campaigns."
                )
        
        # Dormant high-value customers
        dormant_whales = [s for s in results["categories"]["whales"] if s["spending_frequency"] == "dormant"]
        dormant_high = [s for s in results["categories"]["high_spenders"] if s["spending_frequency"] in ["dormant", "inactive"]]
        
        if len(dormant_whales) + len(dormant_high) > 0:
            dormant_value = sum(s["total_spent"] for s in dormant_whales + dormant_high)
            insights.append(
                f"💰 {len(dormant_whales + dormant_high)} high-value customers are inactive. "
                f"They previously spent ${dormant_value/100:.2f} total. Priority for win-back!"
            )
        
        # Purchase patterns
        if stats["total_ppv_purchases"] > 0 and stats["total_tips"] > 0:
            tip_ratio = stats["total_tips"] / (stats["total_ppv_purchases"] + stats["total_tips"]) * 100
            if tip_ratio > 40:
                insights.append(
                    f"💝 Tips make up {tip_ratio:.1f}% of purchases. "
                    f"Your audience appreciates interactive content!"
                )
            elif tip_ratio < 10:
                insights.append(
                    f"📊 Tips are only {tip_ratio:.1f}% of purchases. "
                    f"Consider more interactive engagement to encourage tipping."
                )
        
        # Average spend insights
        if stats["average_spend_per_spender"] > 0:
            avg_dollars = stats["average_spend_per_spender"] / 100
            if avg_dollars > 100:
                insights.append(
                    f"⭐ Excellent average spend of ${avg_dollars:.2f} per spender!"
                )
            elif avg_dollars < 25:
                insights.append(
                    f"📈 Average spend is ${avg_dollars:.2f} per spender. "
                    f"Consider premium content to increase transaction values."
                )
        
        # Conversion rate
        if stats["total_chats"] > 0:
            conversion_rate = (stats["total_spenders"] / stats["total_chats"] * 100)
            if conversion_rate < 20:
                insights.append(
                    f"🎯 Only {conversion_rate:.1f}% of chats have made purchases. "
                    f"Focus on converting non-spenders with targeted offers."
                )
        
        # Trending spenders
        increasing_spenders = [
            s for cat in results["categories"].values() 
            for s in cat 
            if s["spending_trend"] == "increasing" and s["total_spent"] > 2000
        ]
        if increasing_spenders:
            insights.append(
                f"📈 {len(increasing_spenders)} spenders show increasing spend patterns. "
                f"Nurture these relationships!"
            )
        
        if not insights:
            insights.append("✅ Spending patterns appear healthy overall!")
        
        return insights
    
    def export_results(self, results: Dict[str, Any], filename: str = "spender_analysis.json"):
        """Export results to JSON file"""
        output_path = Path(filename)
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=serialize_dates)
        
        logger.info(f"Results exported to {output_path}")
        return output_path


async def main():
    """Main function to run the spender analyzer"""
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
        
        # Create analyzer instance
        analyzer = ActiveSpenderAnalyzer(authed)
        
        # Run the analysis
        results = await analyzer.analyze_all_spenders(
            limit=200,  # Adjust based on your needs
            check_subscriptions=True
        )
        
        # Print summary
        print("\n" + "="*60)
        print("ACTIVE SPENDER ANALYSIS RESULTS")
        print("="*60)
        
        stats = results["statistics"]
        print(f"\nTotal Chats Analyzed: {stats['total_chats']}")
        print(f"Total Spenders: {stats['total_spenders']} ({stats['total_spenders']/stats['total_chats']*100:.1f}%)")
        print(f"Total Revenue: ${stats['total_revenue']/100:.2f}")
        print(f"Average per User: ${stats['average_spend_per_user']/100:.2f}")
        print(f"Average per Spender: ${stats['average_spend_per_spender']/100:.2f}")
        print(f"Active Spenders (7d): {stats['active_spenders_7d']}")
        print(f"Active Spenders (30d): {stats['active_spenders_30d']}")
        
        print("\n" + "-"*40)
        print("SPENDER CATEGORIES:")
        print("-"*40)
        
        for category, users in results["categories"].items():
            if users:
                total_in_cat = sum(u['total_spent'] for u in users)
                print(f"\n{category.replace('_', ' ').title()}: {len(users)} users (${total_in_cat/100:.2f} total)")
                # Show top 3 from each category
                for user in users[:3]:
                    spent = user['total_spent'] / 100
                    status = "📱" if user['is_subscribed'] else "👤"
                    trend = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(user['spending_trend'], "❓")
                    print(f"  {status} @{user['username']} - ${spent:.2f} total, "
                          f"last purchase {user['last_purchase_days_ago']} days ago {trend}")
                if len(users) > 3:
                    print(f"  ... and {len(users) - 3} more")
        
        print("\n" + "-"*40)
        print("TOP 10 SPENDERS:")
        print("-"*40)
        
        for i, spender in enumerate(results["top_spenders"], 1):
            spent = spender['total_spent'] / 100
            ppv = spender['ppv_purchases']
            tips = spender['tip_count']
            score = spender['customer_value_score']
            print(f"\n{i}. @{spender['username']} - ${spent:.2f} (Score: {score}/100)")
            print(f"   PPV: {ppv} | Tips: {tips} | Status: {spender['spending_frequency']}")
        
        print("\n" + "-"*40)
        print("INSIGHTS & RECOMMENDATIONS:")
        print("-"*40)
        
        for insight in results["insights"]:
            print(f"\n{insight}")
        
        # Export results
        export_path = analyzer.export_results(results)
        print(f"\n✅ Full report exported to: {export_path}")
        
        # Actionable recommendations
        print("\n" + "="*60)
        print("IMMEDIATE ACTIONS:")
        print("="*60)
        
        # Find whales who haven't purchased recently
        inactive_whales = [
            s for s in results["categories"]["whales"] 
            if s["last_purchase_days_ago"] > 30
        ]
        if inactive_whales:
            print(f"\n🎯 Re-engage {len(inactive_whales)} inactive whales:")
            for whale in inactive_whales[:5]:
                print(f"   @{whale['username']} - ${whale['total_spent']/100:.2f} lifetime, "
                      f"last purchase {whale['last_purchase_days_ago']} days ago")
        
        # Find users with increasing spend
        trending_up = [
            s for cat in results["categories"].values() 
            for s in cat 
            if s["spending_trend"] == "increasing" and s["spending_frequency"] in ["very_active", "active"]
        ]
        if trending_up:
            print(f"\n💎 Nurture {len(trending_up)} users with increasing spend:")
            for user in trending_up[:5]:
                print(f"   @{user['username']} - ${user['total_spent']/100:.2f} total, "
                      f"score: {user['customer_value_score']}/100")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())