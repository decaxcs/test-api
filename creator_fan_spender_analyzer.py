#!/usr/bin/env python3
"""
Creator Fan Spender Analyzer for OnlyFans
Analyzes YOUR fans' spending patterns to identify your highest value customers
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


class CreatorFanSpenderAnalyzer:
    """Analyzes your fans' spending patterns as a creator"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.current_date = datetime.now(timezone.utc)
        self.creator_id = api_instance.id
        self.creator_username = api_instance.username
    
    def calculate_days_ago(self, date: datetime) -> int:
        """Calculate days between date and now"""
        if not date:
            return -1
        
        # Handle timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        delta = self.current_date - date
        return delta.days
    
    async def analyze_fan_spending(self, chat, message_limit: int = 200) -> Dict[str, Any]:
        """Analyze spending from a single fan"""
        try:
            user = chat.user
            fan_data = {
                "fan_id": user.id,
                "username": user.username,
                "name": user.name,
                "avatar": getattr(user, 'avatar', None),
                "subscription_status": "active",  # If they're in chats, they're likely subscribed
                "total_revenue": 0,
                "ppv_purchases": 0,
                "tips_received": 0,
                "tip_total": 0,
                "messages_purchased": 0,
                "last_purchase_date": None,
                "last_purchase_days_ago": -1,
                "first_purchase_date": None,
                "purchase_history": [],
                "revenue_by_month": defaultdict(float),
                "average_purchase_value": 0,
                "highest_single_purchase": 0,
                "spending_frequency": "never",
                "fan_value_score": 0,
                "spending_trend": "unknown",
                "engagement_level": "low"
            }
            
            # Get messages to analyze their purchases FROM you
            try:
                messages = await user.get_messages(limit=message_limit)
                
                purchases = []
                total_messages = 0
                messages_from_fan = 0
                
                for message in messages:
                    total_messages += 1
                    
                    # Check who sent the message
                    author_id = None
                    if hasattr(message, 'author') and hasattr(message.author, 'id'):
                        author_id = message.author.id
                    elif hasattr(message, 'fromUser') and hasattr(message.fromUser, 'id'):
                        author_id = message.fromUser.id
                    
                    # Count messages from the fan (engagement metric)
                    if author_id == user.id:
                        messages_from_fan += 1
                    
                    # Check if this is a paid message FROM YOU that they purchased
                    price = getattr(message, 'price', 0) or 0
                    if price > 0:
                        is_tip = getattr(message, 'isTip', False)
                        is_opened = getattr(message, 'isOpened', True)
                        
                        # For tips: the fan sent it TO you (author is the fan)
                        # For PPV: you sent it and they opened it (author is you)
                        is_purchase = False
                        purchase_type = None
                        
                        if is_tip and author_id == user.id:
                            # This is a tip FROM the fan TO you
                            is_purchase = True
                            purchase_type = "tip"
                        elif not is_tip and author_id == self.creator_id and is_opened:
                            # This is a PPV you sent that they purchased
                            is_purchase = True
                            purchase_type = "ppv"
                        
                        if is_purchase:
                            purchase = {
                                "message_id": message.id,
                                "amount": price,
                                "amount_dollars": price / 100,
                                "type": purchase_type,
                                "date": message.created_at if hasattr(message, 'created_at') else None,
                                "text_preview": (getattr(message, 'text', '')[:50] + "...") if getattr(message, 'text', '') else "",
                                "media_count": getattr(message, 'media_count', 0)
                            }
                            
                            purchases.append(purchase)
                            fan_data["total_revenue"] += price
                            
                            if purchase_type == "tip":
                                fan_data["tips_received"] += 1
                                fan_data["tip_total"] += price
                            else:
                                fan_data["ppv_purchases"] += 1
                                fan_data["messages_purchased"] += 1
                            
                            # Track highest purchase
                            if price > fan_data["highest_single_purchase"]:
                                fan_data["highest_single_purchase"] = price
                            
                            # Track dates
                            if purchase["date"]:
                                if not fan_data["last_purchase_date"] or purchase["date"] > fan_data["last_purchase_date"]:
                                    fan_data["last_purchase_date"] = purchase["date"]
                                if not fan_data["first_purchase_date"] or purchase["date"] < fan_data["first_purchase_date"]:
                                    fan_data["first_purchase_date"] = purchase["date"]
                                
                                # Track by month
                                month_key = purchase["date"].strftime("%Y-%m")
                                fan_data["revenue_by_month"][month_key] += price
                
                # Calculate engagement level based on messages
                if total_messages > 0:
                    engagement_ratio = messages_from_fan / total_messages
                    if engagement_ratio > 0.3:
                        fan_data["engagement_level"] = "high"
                    elif engagement_ratio > 0.1:
                        fan_data["engagement_level"] = "medium"
                    else:
                        fan_data["engagement_level"] = "low"
                
                # Sort purchases by date (newest first)
                purchases.sort(key=lambda x: x["date"] if x["date"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                fan_data["purchase_history"] = purchases[:20]  # Keep last 20 purchases
                
                # Calculate metrics
                if purchases:
                    fan_data["average_purchase_value"] = fan_data["total_revenue"] / len(purchases)
                    
                    # Calculate days since last purchase
                    if fan_data["last_purchase_date"]:
                        fan_data["last_purchase_days_ago"] = self.calculate_days_ago(fan_data["last_purchase_date"])
                    
                    # Determine spending frequency
                    if fan_data["last_purchase_days_ago"] >= 0:
                        if fan_data["last_purchase_days_ago"] <= 7:
                            fan_data["spending_frequency"] = "very_active"
                        elif fan_data["last_purchase_days_ago"] <= 30:
                            fan_data["spending_frequency"] = "active"
                        elif fan_data["last_purchase_days_ago"] <= 60:
                            fan_data["spending_frequency"] = "moderate"
                        elif fan_data["last_purchase_days_ago"] <= 180:
                            fan_data["spending_frequency"] = "inactive"
                        else:
                            fan_data["spending_frequency"] = "dormant"
                    
                    # Calculate spending trend
                    if len(fan_data["revenue_by_month"]) >= 2:
                        months = sorted(fan_data["revenue_by_month"].keys())
                        recent_months = months[-2:]
                        older_months = months[:-2] if len(months) > 2 else months[:1]
                        
                        recent_avg = sum(fan_data["revenue_by_month"][m] for m in recent_months) / len(recent_months)
                        older_avg = sum(fan_data["revenue_by_month"][m] for m in older_months) / len(older_months) if older_months else 0
                        
                        if older_avg > 0:
                            trend_ratio = recent_avg / older_avg
                            if trend_ratio > 1.5:
                                fan_data["spending_trend"] = "increasing"
                            elif trend_ratio < 0.5:
                                fan_data["spending_trend"] = "decreasing"
                            else:
                                fan_data["spending_trend"] = "stable"
                
                # Calculate fan value score (0-100)
                score = 0
                
                # Total revenue factor (up to 40 points)
                if fan_data["total_revenue"] > 0:
                    if fan_data["total_revenue"] >= 50000:  # $500+
                        score += 40
                    elif fan_data["total_revenue"] >= 20000:  # $200+
                        score += 30
                    elif fan_data["total_revenue"] >= 10000:  # $100+
                        score += 20
                    elif fan_data["total_revenue"] >= 5000:  # $50+
                        score += 10
                    else:
                        score += 5
                
                # Frequency factor (up to 25 points)
                frequency_scores = {
                    "very_active": 25,
                    "active": 20,
                    "moderate": 10,
                    "inactive": 5,
                    "dormant": 0
                }
                score += frequency_scores.get(fan_data["spending_frequency"], 0)
                
                # Tips factor (up to 20 points) - tips show strong engagement
                if fan_data["tips_received"] >= 10:
                    score += 20
                elif fan_data["tips_received"] >= 5:
                    score += 15
                elif fan_data["tips_received"] >= 3:
                    score += 10
                elif fan_data["tips_received"] >= 1:
                    score += 5
                
                # Engagement factor (up to 15 points)
                engagement_scores = {
                    "high": 15,
                    "medium": 10,
                    "low": 5
                }
                score += engagement_scores.get(fan_data["engagement_level"], 0)
                
                fan_data["fan_value_score"] = min(score, 100)
                
            except Exception as e:
                logger.error(f"Error analyzing messages for {user.username}: {e}")
                fan_data["error"] = str(e)
            
            # Convert revenue_by_month to regular dict for JSON serialization
            fan_data["revenue_by_month"] = dict(fan_data["revenue_by_month"])
            
            return fan_data
            
        except Exception as e:
            logger.error(f"Error analyzing fan spending: {e}")
            return None
    
    async def analyze_all_fans(self, limit: int = 200) -> Dict[str, Any]:
        """Analyze spending patterns across all your fans"""
        logger.info("Starting fan spending analysis...")
        
        results = {
            "creator": {
                "username": self.creator_username,
                "id": self.creator_id
            },
            "scan_date": self.current_date.isoformat(),
            "categories": {
                "vip_whales": [],  # $500+ total spend
                "whales": [],  # $200-500
                "high_spenders": [],  # $100-200
                "moderate_spenders": [],  # $50-100
                "low_spenders": [],  # $10-50
                "micro_spenders": [],  # $1-10
                "non_spenders": []  # $0
            },
            "statistics": {
                "total_fans_analyzed": 0,
                "total_paying_fans": 0,
                "total_revenue": 0,
                "total_ppv_revenue": 0,
                "total_tip_revenue": 0,
                "total_ppv_purchases": 0,
                "total_tips": 0,
                "average_revenue_per_fan": 0,
                "average_revenue_per_paying_fan": 0,
                "highest_fan_spend": 0,
                "active_spenders_7d": 0,
                "active_spenders_30d": 0,
                "dormant_spenders": 0,
                "high_engagement_fans": 0
            },
            "insights": [],
            "top_spenders": [],
            "biggest_tippers": [],
            "most_engaged_spenders": []
        }
        
        try:
            # Get all chats (your fans)
            logger.info(f"Fetching up to {limit} fan chats...")
            chats = await self.api.get_chats(limit=limit, offset=0)
            results["statistics"]["total_fans_analyzed"] = len(chats)
            
            # Analyze each fan
            all_fans = []
            logger.info(f"Analyzing {len(chats)} fans for spending patterns...")
            
            for i, chat in enumerate(chats):
                if i % 10 == 0:
                    logger.info(f"Processing fan {i+1}/{len(chats)}...")
                
                try:
                    fan_analysis = await self.analyze_fan_spending(chat)
                    
                    if fan_analysis:
                        # Update statistics
                        if fan_analysis["total_revenue"] > 0:
                            results["statistics"]["total_paying_fans"] += 1
                            results["statistics"]["total_revenue"] += fan_analysis["total_revenue"]
                            results["statistics"]["total_ppv_purchases"] += fan_analysis["ppv_purchases"]
                            results["statistics"]["total_tips"] += fan_analysis["tips_received"]
                            results["statistics"]["total_tip_revenue"] += fan_analysis["tip_total"]
                            results["statistics"]["total_ppv_revenue"] += (fan_analysis["total_revenue"] - fan_analysis["tip_total"])
                            
                            if fan_analysis["last_purchase_days_ago"] <= 7:
                                results["statistics"]["active_spenders_7d"] += 1
                            if fan_analysis["last_purchase_days_ago"] <= 30:
                                results["statistics"]["active_spenders_30d"] += 1
                            if fan_analysis["spending_frequency"] == "dormant":
                                results["statistics"]["dormant_spenders"] += 1
                            
                            if fan_analysis["total_revenue"] > results["statistics"]["highest_fan_spend"]:
                                results["statistics"]["highest_fan_spend"] = fan_analysis["total_revenue"]
                        
                        if fan_analysis["engagement_level"] == "high":
                            results["statistics"]["high_engagement_fans"] += 1
                        
                        # Categorize fan
                        total_spent_dollars = fan_analysis["total_revenue"] / 100
                        if total_spent_dollars >= 500:
                            results["categories"]["vip_whales"].append(fan_analysis)
                        elif total_spent_dollars >= 200:
                            results["categories"]["whales"].append(fan_analysis)
                        elif total_spent_dollars >= 100:
                            results["categories"]["high_spenders"].append(fan_analysis)
                        elif total_spent_dollars >= 50:
                            results["categories"]["moderate_spenders"].append(fan_analysis)
                        elif total_spent_dollars >= 10:
                            results["categories"]["low_spenders"].append(fan_analysis)
                        elif total_spent_dollars >= 1:
                            results["categories"]["micro_spenders"].append(fan_analysis)
                        else:
                            results["categories"]["non_spenders"].append(fan_analysis)
                        
                        all_fans.append(fan_analysis)
                        
                except Exception as e:
                    logger.error(f"Error processing fan: {e}")
            
            # Calculate final statistics
            if results["statistics"]["total_fans_analyzed"] > 0:
                results["statistics"]["average_revenue_per_fan"] = results["statistics"]["total_revenue"] / results["statistics"]["total_fans_analyzed"]
            
            if results["statistics"]["total_paying_fans"] > 0:
                results["statistics"]["average_revenue_per_paying_fan"] = results["statistics"]["total_revenue"] / results["statistics"]["total_paying_fans"]
            
            # Sort categories by value score
            for category in results["categories"]:
                results["categories"][category].sort(
                    key=lambda x: x["fan_value_score"], 
                    reverse=True
                )
            
            # Get top 10 spenders
            all_fans.sort(key=lambda x: x["total_revenue"], reverse=True)
            results["top_spenders"] = all_fans[:10]
            
            # Get biggest tippers
            tipper_fans = [f for f in all_fans if f["tips_received"] > 0]
            tipper_fans.sort(key=lambda x: x["tip_total"], reverse=True)
            results["biggest_tippers"] = tipper_fans[:10]
            
            # Get most engaged paying fans
            engaged_fans = [f for f in all_fans if f["total_revenue"] > 0 and f["engagement_level"] in ["high", "medium"]]
            engaged_fans.sort(key=lambda x: x["fan_value_score"], reverse=True)
            results["most_engaged_spenders"] = engaged_fans[:10]
            
            # Generate insights
            results["insights"] = self.generate_insights(results)
            
            logger.info("Fan spending analysis completed!")
            return results
            
        except Exception as e:
            logger.error(f"Error during fan analysis: {e}")
            raise
    
    def generate_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights for creators"""
        insights = []
        stats = results["statistics"]
        
        # Revenue concentration
        vip_count = len(results["categories"]["vip_whales"])
        whale_count = len(results["categories"]["whales"])
        total_fans = stats["total_fans_analyzed"]
        
        if vip_count + whale_count > 0:
            top_revenue = sum(f["total_revenue"] for f in results["categories"]["vip_whales"] + results["categories"]["whales"])
            top_percent = ((vip_count + whale_count) / total_fans * 100) if total_fans > 0 else 0
            revenue_percent = (top_revenue / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0
            insights.append(
                f"🐋 Your top {vip_count + whale_count} fans ({top_percent:.1f}% of total) "
                f"generate ${top_revenue/100:.2f} ({revenue_percent:.1f}% of revenue)"
            )
        
        # Fan activity
        if stats["total_paying_fans"] > 0:
            active_percent = (stats["active_spenders_30d"] / stats["total_paying_fans"] * 100)
            if active_percent < 50:
                insights.append(
                    f"⚠️ Only {stats['active_spenders_30d']} ({active_percent:.1f}%) of paying fans "
                    f"purchased in the last 30 days. Send exclusive content to re-engage!"
                )
        
        # Tips vs PPV
        if stats["total_revenue"] > 0:
            tip_percent = (stats["total_tip_revenue"] / stats["total_revenue"] * 100)
            if tip_percent > 40:
                insights.append(
                    f"💝 Tips make up {tip_percent:.1f}% of revenue! "
                    f"Your fans love supporting you directly. Keep up the personal engagement!"
                )
            elif tip_percent < 20:
                insights.append(
                    f"📊 Tips are only {tip_percent:.1f}% of revenue. "
                    f"Consider more interactive content to encourage tipping."
                )
        
        # Conversion rate
        if stats["total_fans_analyzed"] > 0:
            conversion_rate = (stats["total_paying_fans"] / stats["total_fans_analyzed"] * 100)
            if conversion_rate < 30:
                insights.append(
                    f"🎯 Only {conversion_rate:.1f}% of fans have made purchases. "
                    f"Try sending targeted PPV to non-spenders."
                )
            elif conversion_rate > 70:
                insights.append(
                    f"⭐ Excellent {conversion_rate:.1f}% conversion rate! "
                    f"Your content strategy is working well."
                )
        
        # Dormant VIPs
        dormant_vips = [
            f for f in results["categories"]["vip_whales"] + results["categories"]["whales"]
            if f["spending_frequency"] in ["inactive", "dormant"]
        ]
        if dormant_vips:
            dormant_revenue = sum(f["total_revenue"] for f in dormant_vips)
            insights.append(
                f"💰 {len(dormant_vips)} high-value fans have gone quiet. "
                f"They spent ${dormant_revenue/100:.2f} total. Send them exclusive content!"
            )
        
        # Engagement insight
        if stats["high_engagement_fans"] > 5:
            engaged_paying = [
                f for f in results["most_engaged_spenders"]
                if f["spending_frequency"] in ["very_active", "active"]
            ]
            if engaged_paying:
                insights.append(
                    f"💬 {len(engaged_paying)} fans are highly engaged AND actively spending. "
                    f"These are your super fans - nurture these relationships!"
                )
        
        if not insights:
            insights.append("✅ Your fan monetization looks healthy overall!")
        
        return insights
    
    def export_results(self, results: Dict[str, Any], filename: str = "fan_spending_analysis.json"):
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
    """Main function to run the creator's fan analyzer"""
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
        
        # Create analyzer instance
        analyzer = CreatorFanSpenderAnalyzer(authed)
        
        # Run the analysis
        results = await analyzer.analyze_all_fans(
            limit=200  # Analyze up to 200 fans
        )
        
        # Print summary
        print("\n" + "="*60)
        print("💰 CREATOR FAN SPENDING ANALYSIS 💰")
        print("="*60)
        print(f"Creator: @{results['creator']['username']}")
        
        stats = results["statistics"]
        print(f"\nTotal Fans Analyzed: {stats['total_fans_analyzed']}")
        print(f"Paying Fans: {stats['total_paying_fans']} ({stats['total_paying_fans']/stats['total_fans_analyzed']*100:.1f}%)")
        print(f"Total Revenue: ${stats['total_revenue']/100:.2f}")
        print(f"  - PPV Revenue: ${stats['total_ppv_revenue']/100:.2f}")
        print(f"  - Tips Revenue: ${stats['total_tip_revenue']/100:.2f}")
        print(f"Average per Fan: ${stats['average_revenue_per_fan']/100:.2f}")
        print(f"Average per Paying Fan: ${stats['average_revenue_per_paying_fan']/100:.2f}")
        print(f"Active Spenders (7d): {stats['active_spenders_7d']}")
        print(f"Active Spenders (30d): {stats['active_spenders_30d']}")
        
        print("\n" + "-"*40)
        print("FAN CATEGORIES:")
        print("-"*40)
        
        for category, fans in results["categories"].items():
            if fans:
                total_in_cat = sum(f['total_revenue'] for f in fans)
                print(f"\n{category.replace('_', ' ').title()}: {len(fans)} fans (${total_in_cat/100:.2f} total)")
                # Show top 3 from each category
                for fan in fans[:3]:
                    revenue = fan['total_revenue'] / 100
                    tips = fan['tips_received']
                    ppv = fan['ppv_purchases']
                    engagement = {"high": "🔥", "medium": "👍", "low": "💤"}.get(fan['engagement_level'], "")
                    trend = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(fan['spending_trend'], "")
                    print(f"  @{fan['username']} - ${revenue:.2f} (PPV:{ppv} Tips:{tips}) {engagement} {trend}")
                if len(fans) > 3:
                    print(f"  ... and {len(fans) - 3} more")
        
        print("\n" + "-"*40)
        print("🏆 TOP 10 SPENDERS:")
        print("-"*40)
        
        for i, fan in enumerate(results["top_spenders"], 1):
            revenue = fan['total_revenue'] / 100
            ppv = fan['ppv_purchases']
            tips = fan['tips_received']
            score = fan['fan_value_score']
            freq = fan['spending_frequency']
            print(f"\n{i}. @{fan['username']} - ${revenue:.2f} (Score: {score}/100)")
            print(f"   PPV: {ppv} | Tips: {tips} | Activity: {freq}")
        
        print("\n" + "-"*40)
        print("💝 TOP TIPPERS:")
        print("-"*40)
        
        for i, fan in enumerate(results["biggest_tippers"][:5], 1):
            tip_total = fan['tip_total'] / 100
            tip_count = fan['tips_received']
            avg_tip = tip_total / tip_count if tip_count > 0 else 0
            print(f"{i}. @{fan['username']} - ${tip_total:.2f} ({tip_count} tips, avg ${avg_tip:.2f})")
        
        print("\n" + "-"*40)
        print("🌟 MOST ENGAGED PAYING FANS:")
        print("-"*40)
        
        for fan in results["most_engaged_spenders"][:5]:
            revenue = fan['total_revenue'] / 100
            engagement = fan['engagement_level']
            freq = fan['spending_frequency']
            print(f"@{fan['username']} - ${revenue:.2f} | Engagement: {engagement} | {freq}")
        
        print("\n" + "-"*40)
        print("💡 INSIGHTS & RECOMMENDATIONS:")
        print("-"*40)
        
        for insight in results["insights"]:
            print(f"\n{insight}")
        
        # Export results
        export_path = analyzer.export_results(results)
        print(f"\n✅ Full report exported to: {export_path}")
        
        # Actionable recommendations
        print("\n" + "="*60)
        print("🎯 IMMEDIATE ACTIONS:")
        print("="*60)
        
        # High-value inactive fans
        inactive_vips = [
            f for f in results["categories"]["vip_whales"] + results["categories"]["whales"]
            if f["last_purchase_days_ago"] > 30
        ]
        if inactive_vips:
            print(f"\n🔥 Send exclusive content to {len(inactive_vips)} inactive VIPs:")
            for vip in inactive_vips[:5]:
                print(f"   @{vip['username']} - ${vip['total_revenue']/100:.2f} lifetime, "
                      f"last purchase {vip['last_purchase_days_ago']} days ago")
        
        # Engaged non-spenders
        engaged_non_spenders = [
            f for f in results["categories"]["non_spenders"]
            if f["engagement_level"] == "high"
        ]
        if engaged_non_spenders:
            print(f"\n💬 Convert {len(engaged_non_spenders)} highly engaged non-spenders:")
            for fan in engaged_non_spenders[:5]:
                print(f"   @{fan['username']} - High engagement but $0 spent")
        
        # Rising stars
        rising_stars = [
            f for cat in ["moderate_spenders", "low_spenders"]
            for f in results["categories"][cat]
            if f["spending_trend"] == "increasing" and f["spending_frequency"] == "very_active"
        ]
        if rising_stars:
            print(f"\n⭐ Nurture {len(rising_stars)} fans with increasing spend:")
            for fan in rising_stars[:5]:
                print(f"   @{fan['username']} - ${fan['total_revenue']/100:.2f} and trending up!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())