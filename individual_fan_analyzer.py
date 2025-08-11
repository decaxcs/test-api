#!/usr/bin/env python3
"""
Individual Fan Analyzer for OnlyFans Creators
Analyzes a specific fan's activity, spending, and engagement patterns
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import sys

from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndividualFanAnalyzer:
    """Comprehensive analyzer for a single fan"""
    
    def __init__(self, api_instance):
        self.api = api_instance
        self.current_date = datetime.now(timezone.utc)
        self.creator_id = api_instance.id
        self.creator_username = api_instance.username
    
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
    
    async def analyze_fan(self, username: str, message_limit: int = 500) -> Dict[str, Any]:
        """Comprehensive analysis of a single fan"""
        logger.info(f"Starting comprehensive analysis for fan: @{username}")
        
        # Get the user
        user = await self.api.get_user(username)
        if not user:
            logger.error(f"User @{username} not found!")
            return None
        
        analysis = {
            "fan_info": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "avatar": getattr(user, 'avatar', None),
                "analysis_date": self.current_date.isoformat()
            },
            "activity_analysis": {
                "first_interaction": None,
                "last_interaction": None,
                "days_since_first_interaction": -1,
                "days_since_last_interaction": -1,
                "total_messages_exchanged": 0,
                "messages_from_fan": 0,
                "messages_from_you": 0,
                "average_messages_per_week": 0,
                "longest_silence_period": 0,
                "current_activity_status": "unknown",
                "interaction_frequency": "unknown",
                "peak_activity_periods": []
            },
            "spending_analysis": {
                "total_spent": 0,
                "total_spent_dollars": 0,
                "ppv_purchases": 0,
                "ppv_total": 0,
                "tips_sent": 0,
                "tips_total": 0,
                "first_purchase_date": None,
                "last_purchase_date": None,
                "days_since_last_purchase": -1,
                "average_purchase_value": 0,
                "highest_single_purchase": 0,
                "lowest_purchase": 999999,
                "spending_frequency": "never",
                "spending_trend": "unknown",
                "monthly_spending": {},
                "purchase_patterns": []
            },
            "engagement_metrics": {
                "response_rate": 0,
                "average_response_time_hours": -1,
                "initiates_conversations": False,
                "conversation_depth": "shallow",
                "engagement_score": 0,
                "loyalty_indicators": []
            },
            "content_interaction": {
                "opened_ppv_count": 0,
                "unopened_ppv_count": 0,
                "ppv_open_rate": 0,
                "preferred_content_type": "unknown",
                "purchase_time_patterns": [],
                "content_preferences": []
            },
            "timeline": [],
            "insights": [],
            "recommendations": []
        }
        
        try:
            # Get all messages for detailed analysis
            logger.info(f"Fetching messages (limit: {message_limit})...")
            messages = await user.get_messages(limit=message_limit)
            
            if not messages:
                logger.warning(f"No messages found with @{username}")
                analysis["activity_analysis"]["current_activity_status"] = "no_interaction"
                analysis["insights"].append("❌ No message history with this fan")
                return analysis
            
            logger.info(f"Analyzing {len(messages)} messages...")
            
            # Process messages chronologically (oldest first)
            messages.reverse()
            
            # Variables for tracking
            all_interactions = []
            purchases = []
            conversations = []
            current_conversation = []
            last_message_time = None
            message_gaps = []
            monthly_messages = {}
            monthly_spending = {}
            response_times = []
            
            for i, message in enumerate(messages):
                msg_time = message.created_at if hasattr(message, 'created_at') else None
                if not msg_time:
                    continue
                
                # Ensure timezone aware
                if msg_time.tzinfo is None:
                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                
                # Determine message author
                author_id = None
                if hasattr(message, 'author') and hasattr(message.author, 'id'):
                    author_id = message.author.id
                elif hasattr(message, 'fromUser') and hasattr(message.fromUser, 'id'):
                    author_id = message.fromUser.id
                
                is_from_fan = (author_id == user.id)
                
                # Track first and last interaction
                if not analysis["activity_analysis"]["first_interaction"]:
                    analysis["activity_analysis"]["first_interaction"] = msg_time
                analysis["activity_analysis"]["last_interaction"] = msg_time
                
                # Count messages
                analysis["activity_analysis"]["total_messages_exchanged"] += 1
                if is_from_fan:
                    analysis["activity_analysis"]["messages_from_fan"] += 1
                else:
                    analysis["activity_analysis"]["messages_from_you"] += 1
                
                # Track monthly activity
                month_key = msg_time.strftime("%Y-%m")
                monthly_messages[month_key] = monthly_messages.get(month_key, 0) + 1
                
                # Track message gaps for silence periods
                if last_message_time:
                    gap_hours = (msg_time - last_message_time).total_seconds() / 3600
                    if gap_hours > 24:  # More than 1 day gap
                        message_gaps.append(gap_hours / 24)  # Convert to days
                    
                    # Track response times
                    if i > 0 and messages[i-1]:
                        prev_author_id = None
                        if hasattr(messages[i-1], 'author') and hasattr(messages[i-1].author, 'id'):
                            prev_author_id = messages[i-1].author.id
                        
                        # If this is a response (different authors)
                        if prev_author_id and prev_author_id != author_id:
                            response_times.append(gap_hours)
                
                # Track conversations
                if not current_conversation or (last_message_time and gap_hours > 12):
                    if current_conversation:
                        conversations.append(current_conversation)
                    current_conversation = [message]
                else:
                    current_conversation.append(message)
                
                last_message_time = msg_time
                
                # Check for purchases (PPV or tips)
                price = getattr(message, 'price', 0) or 0
                if price > 0:
                    is_tip = getattr(message, 'isTip', False)
                    is_opened = getattr(message, 'isOpened', True)
                    
                    # For tips from fan or opened PPV from creator
                    is_purchase = False
                    purchase_type = None
                    
                    if is_tip and is_from_fan:
                        is_purchase = True
                        purchase_type = "tip"
                    elif not is_tip and not is_from_fan and is_opened:
                        is_purchase = True
                        purchase_type = "ppv"
                    elif not is_tip and not is_from_fan and not is_opened:
                        # Track unopened PPV
                        analysis["content_interaction"]["unopened_ppv_count"] += 1
                    
                    if is_purchase:
                        purchase = {
                            "date": msg_time,
                            "amount": price,
                            "amount_dollars": price / 100,
                            "type": purchase_type,
                            "text_preview": (getattr(message, 'text', '')[:50] + "...") if getattr(message, 'text', '') else "",
                            "hour_of_day": msg_time.hour,
                            "day_of_week": msg_time.strftime("%A")
                        }
                        purchases.append(purchase)
                        
                        # Update spending totals
                        analysis["spending_analysis"]["total_spent"] += price
                        
                        if purchase_type == "tip":
                            analysis["spending_analysis"]["tips_sent"] += 1
                            analysis["spending_analysis"]["tips_total"] += price
                        else:
                            analysis["spending_analysis"]["ppv_purchases"] += 1
                            analysis["spending_analysis"]["ppv_total"] += price
                            analysis["content_interaction"]["opened_ppv_count"] += 1
                        
                        # Track monthly spending
                        monthly_spending[month_key] = monthly_spending.get(month_key, 0) + price
                        
                        # Track highest/lowest
                        if price > analysis["spending_analysis"]["highest_single_purchase"]:
                            analysis["spending_analysis"]["highest_single_purchase"] = price
                        if price < analysis["spending_analysis"]["lowest_purchase"]:
                            analysis["spending_analysis"]["lowest_purchase"] = price
                        
                        # Track purchase dates
                        if not analysis["spending_analysis"]["first_purchase_date"]:
                            analysis["spending_analysis"]["first_purchase_date"] = msg_time
                        analysis["spending_analysis"]["last_purchase_date"] = msg_time
                
                # Create timeline entry
                timeline_entry = {
                    "date": msg_time.isoformat(),
                    "type": "message",
                    "from": "fan" if is_from_fan else "you",
                    "text_preview": (getattr(message, 'text', '')[:100] + "...") if getattr(message, 'text', '') else "",
                    "has_media": getattr(message, 'media_count', 0) > 0
                }
                
                if price > 0:
                    timeline_entry["type"] = purchase_type if is_purchase else "ppv_sent"
                    timeline_entry["amount"] = price / 100
                    timeline_entry["purchased"] = is_purchase
                
                all_interactions.append(timeline_entry)
            
            # Add final conversation
            if current_conversation:
                conversations.append(current_conversation)
            
            # Calculate activity metrics
            if analysis["activity_analysis"]["first_interaction"]:
                analysis["activity_analysis"]["days_since_first_interaction"] = self.calculate_days_between(
                    analysis["activity_analysis"]["first_interaction"]
                )
            
            if analysis["activity_analysis"]["last_interaction"]:
                analysis["activity_analysis"]["days_since_last_interaction"] = self.calculate_days_between(
                    analysis["activity_analysis"]["last_interaction"]
                )
            
            # Calculate average messages per week
            if analysis["activity_analysis"]["days_since_first_interaction"] > 0:
                weeks = analysis["activity_analysis"]["days_since_first_interaction"] / 7
                analysis["activity_analysis"]["average_messages_per_week"] = round(
                    analysis["activity_analysis"]["total_messages_exchanged"] / weeks, 1
                )
            
            # Find longest silence period
            if message_gaps:
                analysis["activity_analysis"]["longest_silence_period"] = int(max(message_gaps))
            
            # Determine current activity status
            days_inactive = analysis["activity_analysis"]["days_since_last_interaction"]
            if days_inactive <= 7:
                analysis["activity_analysis"]["current_activity_status"] = "active"
            elif days_inactive <= 30:
                analysis["activity_analysis"]["current_activity_status"] = "semi_active"
            elif days_inactive <= 90:
                analysis["activity_analysis"]["current_activity_status"] = "inactive"
            else:
                analysis["activity_analysis"]["current_activity_status"] = "dormant"
            
            # Determine interaction frequency
            if analysis["activity_analysis"]["average_messages_per_week"] >= 10:
                analysis["activity_analysis"]["interaction_frequency"] = "very_high"
            elif analysis["activity_analysis"]["average_messages_per_week"] >= 5:
                analysis["activity_analysis"]["interaction_frequency"] = "high"
            elif analysis["activity_analysis"]["average_messages_per_week"] >= 2:
                analysis["activity_analysis"]["interaction_frequency"] = "moderate"
            elif analysis["activity_analysis"]["average_messages_per_week"] >= 0.5:
                analysis["activity_analysis"]["interaction_frequency"] = "low"
            else:
                analysis["activity_analysis"]["interaction_frequency"] = "very_low"
            
            # Find peak activity periods
            if monthly_messages:
                sorted_months = sorted(monthly_messages.items(), key=lambda x: x[1], reverse=True)
                analysis["activity_analysis"]["peak_activity_periods"] = [
                    {"month": month, "messages": count} for month, count in sorted_months[:3]
                ]
            
            # Calculate spending metrics
            analysis["spending_analysis"]["total_spent_dollars"] = analysis["spending_analysis"]["total_spent"] / 100
            
            if purchases:
                analysis["spending_analysis"]["average_purchase_value"] = analysis["spending_analysis"]["total_spent"] / len(purchases)
                
                # Days since last purchase
                if analysis["spending_analysis"]["last_purchase_date"]:
                    analysis["spending_analysis"]["days_since_last_purchase"] = self.calculate_days_between(
                        analysis["spending_analysis"]["last_purchase_date"]
                    )
                
                # Spending frequency
                if analysis["spending_analysis"]["days_since_last_purchase"] <= 7:
                    analysis["spending_analysis"]["spending_frequency"] = "very_active"
                elif analysis["spending_analysis"]["days_since_last_purchase"] <= 30:
                    analysis["spending_analysis"]["spending_frequency"] = "active"
                elif analysis["spending_analysis"]["days_since_last_purchase"] <= 90:
                    analysis["spending_analysis"]["spending_frequency"] = "moderate"
                elif analysis["spending_analysis"]["days_since_last_purchase"] <= 180:
                    analysis["spending_analysis"]["spending_frequency"] = "inactive"
                else:
                    analysis["spending_analysis"]["spending_frequency"] = "dormant"
                
                # Analyze purchase patterns
                purchase_hours = [p["hour_of_day"] for p in purchases]
                purchase_days = [p["day_of_week"] for p in purchases]
                
                # Most common purchase times
                if purchase_hours:
                    hour_counts = {}
                    for hour in purchase_hours:
                        time_period = "night" if hour < 6 else "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
                        hour_counts[time_period] = hour_counts.get(time_period, 0) + 1
                    
                    sorted_periods = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                    analysis["content_interaction"]["purchase_time_patterns"] = sorted_periods
                
                # Spending trend
                if len(monthly_spending) >= 2:
                    months = sorted(monthly_spending.keys())
                    recent_months = months[-3:] if len(months) >= 3 else months
                    older_months = months[:-3] if len(months) > 3 else []
                    
                    if older_months:
                        recent_avg = sum(monthly_spending[m] for m in recent_months) / len(recent_months)
                        older_avg = sum(monthly_spending[m] for m in older_months) / len(older_months)
                        
                        if older_avg > 0:
                            trend_ratio = recent_avg / older_avg
                            if trend_ratio > 1.5:
                                analysis["spending_analysis"]["spending_trend"] = "increasing"
                            elif trend_ratio < 0.5:
                                analysis["spending_analysis"]["spending_trend"] = "decreasing"
                            else:
                                analysis["spending_analysis"]["spending_trend"] = "stable"
            
            if analysis["spending_analysis"]["lowest_purchase"] == 999999:
                analysis["spending_analysis"]["lowest_purchase"] = 0
            
            # Calculate engagement metrics
            if analysis["activity_analysis"]["messages_from_you"] > 0:
                analysis["engagement_metrics"]["response_rate"] = round(
                    analysis["activity_analysis"]["messages_from_fan"] / analysis["activity_analysis"]["messages_from_you"] * 100, 1
                )
            
            # Average response time
            if response_times:
                analysis["engagement_metrics"]["average_response_time_hours"] = round(
                    sum(response_times) / len(response_times), 1
                )
            
            # Check if fan initiates conversations
            fan_initiations = 0
            for conv in conversations:
                if conv and hasattr(conv[0], 'author') and conv[0].author.id == user.id:
                    fan_initiations += 1
            
            analysis["engagement_metrics"]["initiates_conversations"] = fan_initiations > len(conversations) * 0.3
            
            # Conversation depth
            if conversations:
                avg_conv_length = sum(len(c) for c in conversations) / len(conversations)
                if avg_conv_length >= 10:
                    analysis["engagement_metrics"]["conversation_depth"] = "deep"
                elif avg_conv_length >= 5:
                    analysis["engagement_metrics"]["conversation_depth"] = "moderate"
                else:
                    analysis["engagement_metrics"]["conversation_depth"] = "shallow"
            
            # Calculate engagement score (0-100)
            score = 0
            
            # Activity frequency (30 points)
            freq_scores = {"very_high": 30, "high": 25, "moderate": 15, "low": 10, "very_low": 5}
            score += freq_scores.get(analysis["activity_analysis"]["interaction_frequency"], 0)
            
            # Response rate (20 points)
            if analysis["engagement_metrics"]["response_rate"] >= 80:
                score += 20
            elif analysis["engagement_metrics"]["response_rate"] >= 50:
                score += 15
            elif analysis["engagement_metrics"]["response_rate"] >= 30:
                score += 10
            elif analysis["engagement_metrics"]["response_rate"] > 0:
                score += 5
            
            # Spending (30 points)
            if analysis["spending_analysis"]["total_spent_dollars"] >= 200:
                score += 30
            elif analysis["spending_analysis"]["total_spent_dollars"] >= 100:
                score += 25
            elif analysis["spending_analysis"]["total_spent_dollars"] >= 50:
                score += 20
            elif analysis["spending_analysis"]["total_spent_dollars"] >= 20:
                score += 15
            elif analysis["spending_analysis"]["total_spent_dollars"] >= 10:
                score += 10
            elif analysis["spending_analysis"]["total_spent_dollars"] > 0:
                score += 5
            
            # Recent activity (20 points)
            if analysis["activity_analysis"]["days_since_last_interaction"] <= 7:
                score += 20
            elif analysis["activity_analysis"]["days_since_last_interaction"] <= 30:
                score += 15
            elif analysis["activity_analysis"]["days_since_last_interaction"] <= 90:
                score += 10
            elif analysis["activity_analysis"]["days_since_last_interaction"] <= 180:
                score += 5
            
            analysis["engagement_metrics"]["engagement_score"] = min(score, 100)
            
            # Identify loyalty indicators
            loyalty_indicators = []
            
            if analysis["activity_analysis"]["days_since_first_interaction"] > 365:
                loyalty_indicators.append("Long-term fan (1+ year)")
            elif analysis["activity_analysis"]["days_since_first_interaction"] > 180:
                loyalty_indicators.append("Established fan (6+ months)")
            
            if analysis["spending_analysis"]["tips_sent"] >= 5:
                loyalty_indicators.append("Regular tipper")
            
            if analysis["engagement_metrics"]["initiates_conversations"]:
                loyalty_indicators.append("Conversation initiator")
            
            if analysis["activity_analysis"]["average_messages_per_week"] >= 5:
                loyalty_indicators.append("Highly engaged")
            
            if analysis["spending_analysis"]["spending_frequency"] in ["very_active", "active"]:
                loyalty_indicators.append("Active spender")
            
            analysis["engagement_metrics"]["loyalty_indicators"] = loyalty_indicators
            
            # Content interaction analysis
            if analysis["content_interaction"]["opened_ppv_count"] + analysis["content_interaction"]["unopened_ppv_count"] > 0:
                analysis["content_interaction"]["ppv_open_rate"] = round(
                    analysis["content_interaction"]["opened_ppv_count"] / 
                    (analysis["content_interaction"]["opened_ppv_count"] + analysis["content_interaction"]["unopened_ppv_count"]) * 100, 1
                )
            
            # Monthly spending conversion
            analysis["spending_analysis"]["monthly_spending"] = {
                month: amount/100 for month, amount in monthly_spending.items()
            }
            
            # Recent timeline (last 20 interactions)
            analysis["timeline"] = all_interactions[-20:]
            analysis["timeline"].reverse()  # Most recent first
            
            # Generate insights
            analysis["insights"] = self.generate_insights(analysis)
            
            # Generate recommendations
            analysis["recommendations"] = self.generate_recommendations(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing fan @{username}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about the fan"""
        insights = []
        
        # Activity insights
        if analysis["activity_analysis"]["current_activity_status"] == "active":
            insights.append(f"✅ Currently active (last seen {analysis['activity_analysis']['days_since_last_interaction']} days ago)")
        elif analysis["activity_analysis"]["current_activity_status"] == "dormant":
            insights.append(f"⚠️ Dormant fan - hasn't interacted in {analysis['activity_analysis']['days_since_last_interaction']} days")
        
        # Spending insights
        if analysis["spending_analysis"]["total_spent_dollars"] > 0:
            insights.append(f"💰 Has spent ${analysis['spending_analysis']['total_spent_dollars']:.2f} total")
            
            if analysis["spending_analysis"]["spending_trend"] == "increasing":
                insights.append("📈 Spending is trending upward!")
            elif analysis["spending_analysis"]["spending_trend"] == "decreasing":
                insights.append("📉 Spending has decreased recently")
        else:
            insights.append("❌ Has never made a purchase")
        
        # Engagement insights
        if analysis["engagement_metrics"]["engagement_score"] >= 80:
            insights.append(f"🌟 Highly engaged fan (score: {analysis['engagement_metrics']['engagement_score']}/100)")
        elif analysis["engagement_metrics"]["engagement_score"] >= 50:
            insights.append(f"👍 Moderately engaged fan (score: {analysis['engagement_metrics']['engagement_score']}/100)")
        
        # Behavior insights
        if analysis["engagement_metrics"]["initiates_conversations"]:
            insights.append("💬 Often starts conversations - very interested!")
        
        if analysis["spending_analysis"]["tips_sent"] > analysis["spending_analysis"]["ppv_purchases"]:
            insights.append("💝 Prefers tipping over PPV purchases")
        elif analysis["spending_analysis"]["ppv_purchases"] > 0:
            insights.append("📦 Regularly purchases PPV content")
        
        # Response patterns
        if analysis["engagement_metrics"]["average_response_time_hours"] > 0:
            if analysis["engagement_metrics"]["average_response_time_hours"] < 2:
                insights.append("⚡ Quick responder (usually within 2 hours)")
            elif analysis["engagement_metrics"]["average_response_time_hours"] < 24:
                insights.append(f"⏱️ Responds within {analysis['engagement_metrics']['average_response_time_hours']:.1f} hours on average")
        
        # Purchase timing
        if analysis["content_interaction"]["purchase_time_patterns"]:
            top_time = analysis["content_interaction"]["purchase_time_patterns"][0]
            insights.append(f"🕐 Most active during {top_time[0]} hours")
        
        return insights
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on activity status
        if analysis["activity_analysis"]["current_activity_status"] == "dormant":
            if analysis["spending_analysis"]["total_spent_dollars"] > 100:
                recommendations.append("🎯 HIGH PRIORITY: This is a dormant high-value fan. Send exclusive content to re-engage!")
            else:
                recommendations.append("📨 Send a personalized message to re-engage this dormant fan")
        
        elif analysis["activity_analysis"]["current_activity_status"] == "inactive":
            recommendations.append("💌 Send a 'miss you' message with special offer")
        
        # Based on spending patterns
        if analysis["spending_analysis"]["spending_frequency"] == "very_active":
            recommendations.append("🔥 Strike while hot! This fan is actively spending - send premium content")
        
        if analysis["spending_analysis"]["tips_sent"] > 3:
            recommendations.append("💝 This fan loves tipping - increase personal interaction")
        
        if analysis["content_interaction"]["ppv_open_rate"] < 50 and analysis["content_interaction"]["unopened_ppv_count"] > 0:
            recommendations.append(f"📦 {analysis['content_interaction']['unopened_ppv_count']} unopened PPVs - try lower price points")
        
        # Based on engagement
        if analysis["engagement_metrics"]["engagement_score"] >= 70 and analysis["spending_analysis"]["total_spent_dollars"] < 50:
            recommendations.append("💎 Highly engaged but low spend - perfect for conversion campaign")
        
        if analysis["engagement_metrics"]["conversation_depth"] == "deep":
            recommendations.append("💬 This fan values conversation - maintain personal touch")
        
        # Time-based recommendations
        if analysis["content_interaction"]["purchase_time_patterns"]:
            top_time = analysis["content_interaction"]["purchase_time_patterns"][0][0]
            recommendations.append(f"⏰ Send PPV content during {top_time} for best results")
        
        # Loyalty recommendations
        if len(analysis["engagement_metrics"]["loyalty_indicators"]) >= 3:
            recommendations.append("👑 This is a loyal fan - consider VIP perks or exclusive content")
        
        # Trend-based
        if analysis["spending_analysis"]["spending_trend"] == "decreasing":
            recommendations.append("📉 Spending declining - send exclusive offer to reverse trend")
        elif analysis["spending_analysis"]["spending_trend"] == "increasing":
            recommendations.append("📈 Spending increasing - capitalize with premium offerings")
        
        return recommendations
    
    def export_report(self, analysis: Dict[str, Any], filename: str = None):
        """Export analysis to JSON file"""
        if not filename:
            username = analysis["fan_info"]["username"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fan_analysis_{username}_{timestamp}.json"
        
        output_path = Path(filename)
        
        # Convert datetime objects to strings
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=serialize_dates)
        
        logger.info(f"Report exported to {output_path}")
        return output_path


async def main():
    """Main function to run individual fan analyzer"""
    try:
        # Get username from command line or prompt
        if len(sys.argv) > 1:
            target_username = sys.argv[1]
        else:
            target_username = input("Enter fan username to analyze: ").strip()
            if not target_username:
                logger.error("No username provided!")
                return
        
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
        analyzer = IndividualFanAnalyzer(authed)
        
        # Run analysis
        analysis = await analyzer.analyze_fan(target_username)
        
        if not analysis:
            logger.error(f"Failed to analyze @{target_username}")
            return
        
        # Print results
        print("\n" + "="*70)
        print(f"🔍 FAN ANALYSIS: @{analysis['fan_info']['username']}")
        print("="*70)
        
        # Basic info
        print(f"\n👤 Fan: {analysis['fan_info']['name']} (@{analysis['fan_info']['username']})")
        print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Activity Summary
        activity = analysis["activity_analysis"]
        print(f"\n📊 ACTIVITY SUMMARY:")
        print(f"  Status: {activity['current_activity_status'].replace('_', ' ').title()}")
        print(f"  First Interaction: {activity['days_since_first_interaction']} days ago")
        print(f"  Last Interaction: {activity['days_since_last_interaction']} days ago")
        print(f"  Total Messages: {activity['total_messages_exchanged']}")
        print(f"    - From Fan: {activity['messages_from_fan']}")
        print(f"    - From You: {activity['messages_from_you']}")
        print(f"  Interaction Frequency: {activity['interaction_frequency'].replace('_', ' ').title()}")
        print(f"  Avg Messages/Week: {activity['average_messages_per_week']}")
        
        # Spending Summary
        spending = analysis["spending_analysis"]
        print(f"\n💰 SPENDING SUMMARY:")
        print(f"  Total Spent: ${spending['total_spent_dollars']:.2f}")
        print(f"    - PPV: ${spending['ppv_total']/100:.2f} ({spending['ppv_purchases']} purchases)")
        print(f"    - Tips: ${spending['tips_total']/100:.2f} ({spending['tips_sent']} tips)")
        if spending['total_spent_dollars'] > 0:
            print(f"  Average Purchase: ${spending['average_purchase_value']/100:.2f}")
            print(f"  Highest Purchase: ${spending['highest_single_purchase']/100:.2f}")
            print(f"  Last Purchase: {spending['days_since_last_purchase']} days ago")
            print(f"  Spending Status: {spending['spending_frequency'].replace('_', ' ').title()}")
            print(f"  Spending Trend: {spending['spending_trend'].title()}")
        
        # Engagement Metrics
        engagement = analysis["engagement_metrics"]
        print(f"\n🎯 ENGAGEMENT METRICS:")
        print(f"  Engagement Score: {engagement['engagement_score']}/100")
        print(f"  Response Rate: {engagement['response_rate']}%")
        if engagement['average_response_time_hours'] > 0:
            print(f"  Avg Response Time: {engagement['average_response_time_hours']:.1f} hours")
        print(f"  Initiates Conversations: {'Yes' if engagement['initiates_conversations'] else 'No'}")
        print(f"  Conversation Depth: {engagement['conversation_depth'].title()}")
        
        # Loyalty Indicators
        if engagement['loyalty_indicators']:
            print(f"\n🏆 LOYALTY INDICATORS:")
            for indicator in engagement['loyalty_indicators']:
                print(f"  ✓ {indicator}")
        
        # Content Interaction
        content = analysis["content_interaction"]
        if content['opened_ppv_count'] + content['unopened_ppv_count'] > 0:
            print(f"\n📦 CONTENT INTERACTION:")
            print(f"  PPV Open Rate: {content['ppv_open_rate']}%")
            print(f"  Opened PPVs: {content['opened_ppv_count']}")
            print(f"  Unopened PPVs: {content['unopened_ppv_count']}")
        
        # Insights
        print(f"\n💡 INSIGHTS:")
        for insight in analysis['insights']:
            print(f"  {insight}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # Recent Activity
        if analysis['timeline']:
            print(f"\n📅 RECENT ACTIVITY (Last 5):")
            for event in analysis['timeline'][:5]:
                date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                date_str = date.strftime('%Y-%m-%d %H:%M')
                if event['type'] == 'message':
                    print(f"  {date_str} - Message from {event['from']}")
                elif event['type'] in ['tip', 'ppv']:
                    status = "✅" if event.get('purchased') else "❌"
                    print(f"  {date_str} - {event['type'].upper()} ${event.get('amount', 0):.2f} {status}")
        
        # Export report
        export_path = analyzer.export_report(analysis)
        print(f"\n✅ Full report exported to: {export_path}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if 'api' in locals():
            await api.close_pools()


if __name__ == "__main__":
    asyncio.run(main())