"""
AI Insights Engine using OpenRouter API

Safe, cost-controlled AI analysis with:
- Structured prompts (no hallucinations)
- Error handling and fallbacks
- No calculations in AI (pure explanation)
- JSON response validation
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("finance_companion_key")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-3.5-turbo"
MAX_TOKENS = 800
TIMEOUT = 10


async def call_openrouter(messages: list) -> Optional[str]:
    """
    Safe call to OpenRouter API with error handling.
    
    Args:
        messages: List of message dicts with "role" and "content"
        
    Returns:
        Response text or None if error
    """
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "max_tokens": MAX_TOKENS,
                    "temperature": 0.7,
                }
            )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code}")
            return None
        
        data = response.json()
        result = data.get("choices", [{}])[0].get("message", {}).get("content")
        
        return result
    
    except httpx.TimeoutException:
        logger.error("OpenRouter API timeout")
        return None
    except Exception as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        return None


def validate_json_response(response_text: str) -> Optional[Dict]:
    """
    Safely parse JSON response from AI.
    
    Args:
        response_text: Raw response from AI
        
    Returns:
        Parsed dict or None if invalid
    """
    if not response_text:
        return None
    
    try:
        # Try to find JSON in response (in case AI adds extra text)
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            return None
        
        json_str = response_text[start:end]
        data = json.loads(json_str)
        
        return data
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from AI response")
        return None


async def generate_spending_insights(summary_data: dict) -> dict:
    """
    Analyze spending patterns and suggest improvements.
    
    Args:
        summary_data: Output from get_spending_summary()
        
    Returns:
        {
            "insights": ["observation text"],
            "suggestions": ["suggestion 1", "suggestion 2"],
            "model": "gpt-3.5-turbo"
        }
    """
    
    if not summary_data.get("total_spent"):
        return {
            "insights": ["Insufficient spending data for analysis"],
            "suggestions": ["Start tracking your expenses to get insights"],
            "model": "fallback"
        }
    
    # Build prompt with actual numbers
    top_cat = summary_data.get("top_category", "Unknown")
    top_amount = summary_data.get("category_breakdown", {}).get(top_cat, 0)
    weekday_avg = summary_data.get("weekday_vs_weekend", {}).get("weekday_average", 0)
    weekend_avg = summary_data.get("weekday_vs_weekend", {}).get("weekend_average", 0)
    total_spent = summary_data['total_spent']
    expense_count = summary_data['expense_count']
    
    prompt = f"""You are a friendly personal finance advisor having a conversation with someone about their spending habits. Be warm, encouraging, and use casual language like you're talking to a friend.

Your friend just showed you their spending from the last 30 days:
- They spent ₹{total_spent:,.0f} total across {expense_count} transactions
- Most of it went to {top_cat} (₹{top_amount:,.0f})
- They spend about ₹{weekday_avg:,.0f} on weekdays vs ₹{weekend_avg:,.0f} on weekends

Have a friendly conversation about what you notice. Be encouraging if they're doing well, or gently point out areas to improve. Use "you" and "your" to make it personal.

Respond with ONLY valid JSON. No extra text.

{{
  "pattern": "A friendly observation about their spending pattern (use conversational language, 2-3 sentences)",
  "suggestions": [
    "First piece of friendly advice (be specific and actionable, 2-3 sentences)",
    "Second piece of friendly advice (be specific and actionable, 2-3 sentences)"
  ]
}}"""
    
    response_text = await call_openrouter([
        {"role": "system", "content": "You are a warm, friendly personal finance buddy who gives encouraging yet honest advice. Use conversational language. Respond ONLY with valid JSON object."},
        {"role": "user", "content": prompt}
    ])
    
    if not response_text:
        return {
            "insights": ["Unable to analyze at this time"],
            "suggestions": ["Continue tracking expenses regularly"],
            "model": "fallback"
        }
    
    # Parse response
    parsed = validate_json_response(response_text)
    
    if not parsed:
        return {
            "insights": ["Analysis complete but formatting unavailable"],
            "suggestions": ["Monitor your top spending categories"],
            "model": "fallback"
        }
    
    return {
        "insights": [parsed.get("pattern", "")],
        "suggestions": parsed.get("suggestions", []),
        "model": MODEL
    }


async def explain_what_if_impact(
    current_data: dict,
    scenario_data: dict
) -> dict:
    """
    Explain impact of spending change on savings and sustainability.
    
    Args:
        current_data: {"monthly_income", "monthly_expense", "monthly_savings"}
        scenario_data: {"category", "percent_change", "new_category_amount", 
                       "new_total_expense", "new_savings", "new_savings_rate"}
        
    Returns:
        {
            "sustainable": bool,
            "impact": "explanation text",
            "risk_level": "low|medium|high",
            "recommendation": "one practical suggestion"
        }
    """
    
    income = current_data['monthly_income']
    current_savings = current_data['monthly_savings']
    category = scenario_data['category']
    percent_change = scenario_data['percent_change']
    new_savings = scenario_data['new_savings']
    new_savings_rate = scenario_data['new_savings_rate']
    savings_impact = scenario_data.get('savings_impact', 0)
    
    # Determine direction of change
    direction = "down" if percent_change < 0 else "up"
    abs_percent = abs(percent_change)
    
    # Determine impact on savings
    if savings_impact > 0:
        impact_direction = "increase"
        impact_verb = "would increase"
    else:
        impact_direction = "decrease"
        impact_verb = "would decrease"
    
    prompt = f"""You are a friendly personal finance buddy helping someone think through a "what if" scenario. Talk to them like a friend who cares about their financial future.

Their situation right now:
- They earn ₹{income:,.0f} per month
- They're saving ₹{current_savings:,.0f} every month (that's awesome!)

They want to know: "What if my {category} expenses go {direction} by {abs_percent}%?"

The math shows:
- Their savings would {impact_verb} to ₹{new_savings:,.0f} per month
- That's a ₹{abs(savings_impact):,.0f} {impact_direction} in what they can save
- Their new savings rate would be {new_savings_rate:.1f}%

Give them a real, human response. Explain what this change means for their money in a way they can actually understand and feel. Be encouraging but honest.

Respond with ONLY valid JSON. No extra text.

{{
  "sustainable": true or false (can they still handle their bills and goals with this change?),
  "impact": "Explain what this change means for them in plain English, like you're talking face-to-face (3-4 sentences max)",
  "risk_level": "low, medium, or high",
  "recommendation": "One specific, actionable thing they should do about this scenario (2-3 sentences, be personal and helpful)"
}}"""
    
    response_text = await call_openrouter([
        {"role": "system", "content": "You are a caring friend who helps people understand money decisions in plain English. Be warm, encouraging, and real. Respond ONLY with valid JSON object."},
        {"role": "user", "content": prompt}
    ])
    
    if not response_text:
        return {
            "sustainable": scenario_data['new_savings'] > 0,
            "impact": "Impact analysis unavailable",
            "risk_level": "unknown",
            "recommendation": "Review your financial plan",
            "model": "fallback"
        }
    
    # Parse response
    parsed = validate_json_response(response_text)
    
    if not parsed:
        # Return calculated values even if AI fails
        return {
            "sustainable": scenario_data['new_savings'] > 0,
            "impact": f"New savings rate would be {scenario_data['new_savings_rate']:.1f}%",
            "risk_level": "unknown",
            "recommendation": "Consult your financial goals",
            "model": "fallback"
        }
    
    # Ensure risk_level is valid
    risk_level = parsed.get("risk_level", "unknown").lower()
    if risk_level not in ["low", "medium", "high", "unknown"]:
        risk_level = "unknown"
    
    return {
        "sustainable": parsed.get("sustainable", scenario_data['new_savings'] > 0),
        "impact": parsed.get("impact", ""),
        "risk_level": risk_level,
        "recommendation": parsed.get("recommendation", ""),
        "model": MODEL
    }
