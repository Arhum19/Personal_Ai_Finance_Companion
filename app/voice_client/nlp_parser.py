"""
NLP Parser for Voice Client
Parses transcribed text into structured expense/income/goal/contribution data
"""
import re
from datetime import datetime
from word2number import w2n
import dateparser

from .config import (
    DEFAULT_CATEGORIES, 
    INCOME_KEYWORDS, 
    INCOME_SOURCES, 
    NUMBER_WORDS,
    GOAL_KEYWORDS,
    CONTRIBUTION_KEYWORDS
)


def detect_intent(text: str) -> str:
    """
    Detect whether the text represents an INCOME, EXPENSE, GOAL, or CONTRIBUTION.
    Returns: 'income', 'expense', 'goal', or 'contribution'
    """
    text_lower = text.lower()
    
    # Check for contribution keywords first (highest priority)
    for keyword in CONTRIBUTION_KEYWORDS:
        if keyword in text_lower:
            return 'contribution'
    
    # Check for goal keywords
    for keyword in GOAL_KEYWORDS:
        if keyword in text_lower:
            return 'goal'
    
    # Check for income keywords
    for keyword in INCOME_KEYWORDS:
        if keyword in text_lower:
            return 'income'
    
    return 'expense'


def extract_amount(text: str) -> float | None:
    """
    Extract numeric amount from text.
    Handles both digit numbers (500, 6000) and word numbers (five hundred).
    """
    # Remove commas and clean text
    clean_text = text.replace(',', '')
    
    # 1) Try to find digit numbers first (e.g., "500", "6000.50")
    match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # 2) Try to convert word numbers (e.g., "five hundred", "two thousand")
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    current = []
    candidates = []
    
    for tok in tokens:
        if tok in NUMBER_WORDS:
            current.append(tok)
        else:
            if current:
                candidates.append(" ".join(current))
                current = []
    
    if current:
        candidates.append(" ".join(current))
    
    for cand in candidates:
        try:
            num = w2n.word_to_num(cand)
            return float(num)
        except Exception:
            continue
    
    return None


def extract_date(text: str) -> str:
    """
    Extract date from text using dateparser.
    Returns ISO format datetime string.
    """
    # Define date keywords to look for
    date_patterns = r'\b(today|yesterday|tomorrow|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s+\d{2,4})?|last\s+\w+|\d+\s+days?\s+ago)\b'
    
    # First try to extract date-related phrases
    match = re.search(date_patterns, text.lower())
    if match:
        date_phrase = match.group(0)
        dt = dateparser.parse(date_phrase, settings={'PREFER_DATES_FROM': 'past'})
        if dt:
            return dt.isoformat()
    
    # Fallback: try parsing entire text
    dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'past'})
    if dt:
        return dt.isoformat()
    
    # Default to current datetime
    return datetime.now().isoformat()


def extract_category(text: str) -> str:
    """
    Extract expense category from text using keyword matching.
    Returns category name (lowercase).
    """
    text_lower = text.lower()
    
    for category, keywords in DEFAULT_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return 'other'


def extract_income_source(text: str) -> str:
    """
    Extract income source from text using keyword matching.
    Returns source name.
    """
    text_lower = text.lower()
    
    for source, keywords in INCOME_SOURCES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return source.capitalize()
    
    return 'Other'


def extract_goal_title(text: str) -> str:
    """
    Extract goal title from text.
    Tries to identify what the user wants to buy/save for.
    
    Examples:
    - "I want to buy laptop for 50000" -> "Buy Laptop"
    - "Goal: save for vacation 100000" -> "Vacation"
    - "Save for new phone 30000" -> "New Phone"
    """
    text_lower = text.lower()
    
    # Patterns to extract the goal subject
    patterns = [
        r'(?:want to |wanna |gonna |going to )(?:buy|get|purchase|save for)\s+(?:a\s+)?(.+?)(?:\s+for|\s+worth|\s+at|\s+\d|$)',
        r'(?:buy|get|purchase)\s+(?:a\s+)?(.+?)(?:\s+for|\s+worth|\s+\d|$)',
        r'(?:save for|saving for|save up for)\s+(?:a\s+)?(.+?)(?:\s+for|\s+worth|\s+\d|$)',
        r'goal[:\s]+(.+?)(?:\s+for|\s+worth|\s+\d|$)',
        r'target[:\s]+(.+?)(?:\s+for|\s+worth|\s+\d|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            title = match.group(1).strip()
            # Clean up and capitalize
            title = re.sub(r'\s+', ' ', title)  # Normalize spaces
            title = title.strip('.,!? ')
            if title and len(title) > 1:
                return title.title()  # Capitalize first letter of each word
    
    # Fallback: try to find common goal items
    goal_items = {
        'laptop': 'Buy Laptop',
        'phone': 'Buy Phone',
        'car': 'Buy Car',
        'bike': 'Buy Bike',
        'vacation': 'Vacation Fund',
        'holiday': 'Holiday Fund',
        'trip': 'Trip Fund',
        'wedding': 'Wedding Fund',
        'house': 'House Fund',
        'home': 'Home Fund',
        'education': 'Education Fund',
        'course': 'Course Fee',
        'emergency': 'Emergency Fund',
        'iphone': 'Buy iPhone',
        'macbook': 'Buy MacBook',
        'watch': 'Buy Watch',
        'camera': 'Buy Camera',
        'tv': 'Buy TV',
        'playstation': 'Buy PlayStation',
        'xbox': 'Buy Xbox',
    }
    
    for item, title in goal_items.items():
        if item in text_lower:
            return title
    
    # Ultimate fallback
    return 'Savings Goal'


def extract_goal_name_for_contribution(text: str) -> str:
    """
    Extract goal name from a contribution statement.
    
    Examples:
    - "Contribute 5000 to laptop goal" -> "laptop"
    - "Add 10000 to my vacation fund" -> "vacation"
    - "Put 2000 towards car" -> "car"
    """
    text_lower = text.lower()
    
    # Patterns to extract goal name from contribution
    patterns = [
        r'(?:to|towards|for)\s+(?:my\s+)?(?:the\s+)?(.+?)(?:\s+goal|\s+fund|\s*$)',
        r'(?:contribute|add|put|allocate|deposit|save)\s+\d+\s+(?:to|towards|for)\s+(?:my\s+)?(.+?)(?:\s+goal|\s+fund|\s*$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            goal_name = match.group(1).strip()
            goal_name = re.sub(r'\s+', ' ', goal_name)
            goal_name = goal_name.strip('.,!? ')
            if goal_name and len(goal_name) > 1:
                return goal_name.lower()
    
    # Fallback: look for common goal item names
    goal_items = ['laptop', 'phone', 'car', 'bike', 'vacation', 'holiday', 'trip', 
                  'wedding', 'house', 'home', 'education', 'emergency', 'iphone', 
                  'macbook', 'watch', 'camera', 'tv', 'playstation', 'xbox']
    
    for item in goal_items:
        if item in text_lower:
            return item
    
    return None  # Couldn't identify goal


def generate_title(text: str, category: str) -> str:
    """
    Generate a short title for the expense.
    """
    # Capitalize category as base title
    title = category.capitalize()
    
    # Try to extract more specific context
    text_lower = text.lower()
    
    # Look for specific items mentioned
    specific_items = {
        'pizza': 'Pizza',
        'burger': 'Burger',
        'coffee': 'Coffee',
        'uber': 'Uber Ride',
        'taxi': 'Taxi Ride',
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'amazon': 'Amazon Order',
        'electricity': 'Electricity Bill',
        'rent': 'Rent Payment',
        'gym': 'Gym Membership',
        'medicine': 'Medicine',
        'grocery': 'Groceries',
        'petrol': 'Petrol/Fuel',
        'recharge': 'Mobile Recharge',
    }
    
    for item, item_title in specific_items.items():
        if item in text_lower:
            return item_title
    
    return title


def parse_text(text: str) -> dict:
    """
    Main parsing function.
    Takes transcribed text and returns structured data.
    
    Args:
        text: Transcribed text from Whisper
        
    Returns:
        dict with type, amount, category/source/title/goal_name, description, date
    """
    if not text or not text.strip():
        return {
            "type": None,
            "error": "Empty or invalid text"
        }
    
    # Detect intent (income, expense, goal, or contribution)
    intent = detect_intent(text)
    
    # Extract amount
    amount = extract_amount(text)
    
    # Extract date
    date_iso = extract_date(text)
    
    if intent == 'contribution':
        goal_name = extract_goal_name_for_contribution(text)
        return {
            "type": "contribution",
            "amount": amount,
            "goal_name": goal_name,  # Needs to be matched to goal_id later
            "description": text,
            "date": date_iso
        }
    elif intent == 'goal':
        title = extract_goal_title(text)
        return {
            "type": "goal",
            "title": title,
            "amount": amount,
            "description": text,
            "date": date_iso
        }
    elif intent == 'income':
        source = extract_income_source(text)
        return {
            "type": "income",
            "amount": amount,
            "source": source,
            "description": text,
            "date": date_iso
        }
    else:
        category = extract_category(text)
        title = generate_title(text, category)
        return {
            "type": "expense",
            "title": title,
            "amount": amount,
            "category": category,
            "description": text,
            "date": date_iso
        }


def format_parsed_data(parsed: dict) -> str:
    """
    Format parsed data for display to user.
    """
    if parsed.get("error"):
        return f"❌ Error: {parsed['error']}"
    
    if parsed["type"] == "contribution":
        amount_str = f"₹{parsed['amount']:,.2f}" if parsed['amount'] else "Not detected"
        goal_name = parsed.get('goal_name', 'Unknown')
        return (
            f"💵 CONTRIBUTION Detected:\n"
            f"   Amount: {amount_str}\n"
            f"   To Goal: {goal_name.title() if goal_name else 'Not detected'}\n"
            f"   Description: {parsed['description']}"
        )
    elif parsed["type"] == "goal":
        amount_str = f"₹{parsed['amount']:,.2f}" if parsed['amount'] else "Not detected"
        return (
            f"🎯 GOAL Detected:\n"
            f"   Title: {parsed['title']}\n"
            f"   Target Amount: {amount_str}\n"
            f"   Description: {parsed['description']}"
        )
    elif parsed["type"] == "income":
        return (
            f"💰 INCOME Detected:\n"
            f"   Amount: ₹{parsed['amount']:,.2f}\n" if parsed['amount'] else "   Amount: Not detected\n"
            f"   Source: {parsed['source']}\n"
            f"   Date: {parsed['date'][:10]}\n"
            f"   Description: {parsed['description']}"
        )
    else:
        amount_str = f"₹{parsed['amount']:,.2f}" if parsed['amount'] else "Not detected"
        return (
            f"💸 EXPENSE Detected:\n"
            f"   Title: {parsed['title']}\n"
            f"   Amount: {amount_str}\n"
            f"   Category: {parsed['category'].capitalize()}\n"
            f"   Date: {parsed['date'][:10]}\n"
            f"   Description: {parsed['description']}"
        )


# Quick test
if __name__ == "__main__":
    test_cases = [
        "I spent 6000 on shopping yesterday",
        "I got paid 50000 salary today",
        "Paid 500 for uber yesterday",
        "Received 15000 from freelance project",
        "Bought groceries for five hundred rupees",
        "Netflix subscription for 199",
        "Got bonus of 10000",
        # Goal test cases
        "I want to buy laptop for 50000",
        "Goal: save for vacation 100000",
        "Save for new phone 30000",
        "I want to save for emergency fund 200000",
        "Planning to buy a car for 500000",
        # Contribution test cases
        "Contribute 5000 to laptop goal",
        "Add 10000 to my vacation fund",
        "Put 2000 towards car",
        "Allocate 15000 to emergency fund",
    ]
    
    print("=" * 60)
    print("NLP Parser Test")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\nInput: \"{text}\"")
        result = parse_text(text)
        print(format_parsed_data(result))
        print("-" * 40)
