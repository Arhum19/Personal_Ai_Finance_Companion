"""
NLP Parser for Voice Client
Parses transcribed text into structured expense/income data
"""
import re
from datetime import datetime
from word2number import w2n
import dateparser

from .config import (
    DEFAULT_CATEGORIES, 
    INCOME_KEYWORDS, 
    INCOME_SOURCES, 
    NUMBER_WORDS
)


def detect_intent(text: str) -> str:
    """
    Detect whether the text represents an INCOME or EXPENSE.
    Returns: 'income' or 'expense'
    """
    text_lower = text.lower()
    
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
        dict with type, amount, category/source, description, date, title
    """
    if not text or not text.strip():
        return {
            "type": None,
            "error": "Empty or invalid text"
        }
    
    # Detect intent (income or expense)
    intent = detect_intent(text)
    
    # Extract amount
    amount = extract_amount(text)
    
    # Extract date
    date_iso = extract_date(text)
    
    if intent == 'income':
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
    
    if parsed["type"] == "income":
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
    ]
    
    print("=" * 60)
    print("NLP Parser Test")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\nInput: \"{text}\"")
        result = parse_text(text)
        print(format_parsed_data(result))
        print("-" * 40)
