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
    CONTRIBUTION_KEYWORDS,
    EXPENSE_KEYWORDS
)


def detect_intent(text: str) -> str:
    """
    Detect whether the text represents an INCOME, EXPENSE, GOAL, or CONTRIBUTION.
    Returns: 'income', 'expense', 'goal', or 'contribution'
    
    Priority order and logic:
    1. CONTRIBUTION - Adding money to an EXISTING goal (highest specificity)
    2. GOAL - Creating a NEW savings goal
    3. INCOME - Money received
    4. EXPENSE - Money spent (default)
    """
    text_lower = text.lower().strip()
    
    # Calculate match scores for each intent type
    contribution_score = 0
    goal_score = 0
    income_score = 0
    expense_score = 0
    
    # ===== CONTRIBUTION DETECTION (highest priority) =====
    # Key differentiator: Contributing to EXISTING goal vs creating NEW goal
    contribution_strong_indicators = [
        'contribute', 'contributing', 'contribution',
        'add to goal', 'add to my goal', 'adding to goal',
        'add to my', 'adding to my',
        'put towards', 'putting towards',
        'deposit to goal', 'depositing to goal',
        'transfer to goal', 'move to goal',
        'fund my goal', 'funding my',
        'top up', 'topping up',
        'towards my fund', 'to my fund', 'into my fund',
        'towards my goal', 'to my goal', 'into my goal',
    ]
    
    for indicator in contribution_strong_indicators:
        if indicator in text_lower:
            contribution_score += 10
    
    # Check for contribution keywords from config
    for keyword in CONTRIBUTION_KEYWORDS:
        if keyword in text_lower:
            contribution_score += 3
    
    # Boost if mentions existing goal-like items with "add/put/contribute"
    existing_goal_items = ['laptop', 'car', 'vacation', 'phone', 'emergency', 'house', 'bike', 'wedding', 'trip']
    action_words = ['add', 'put', 'contribute', 'deposit', 'transfer', 'allocate']
    
    for item in existing_goal_items:
        if item in text_lower:
            for action in action_words:
                if action in text_lower:
                    # Pattern like "add 5000 to laptop" or "contribute to car"
                    contribution_score += 5
                    break
    
    # ===== GOAL DETECTION =====
    # Key differentiator: Creating NEW goal, future intent, planning
    goal_strong_indicators = [
        'create goal', 'new goal', 'set goal', 'make goal', 'start goal',
        'want to buy', 'wanna buy', 'gonna buy', 'going to buy', 'planning to buy',
        'want to get', 'wanna get', 'gonna get', 'going to get',
        'save for', 'saving for', 'save up for', 'saving up for',
        'need to save', 'want to save', 'start saving',
        'dream of', 'dream to', 'wish to buy', 'hoping to',
        'looking to buy', 'thinking of buying', 'plan to buy',
        'set target', 'my target', 'aim to',
        'goal for', 'goal to buy', 'goal is to',
        'budget for', 'budgeting for',
        'i want', 'i need', 'i wish',
    ]
    
    for indicator in goal_strong_indicators:
        if indicator in text_lower:
            goal_score += 10
    
    # Check for goal keywords from config
    for keyword in GOAL_KEYWORDS:
        if keyword in text_lower:
            goal_score += 3
    
    # Future tense indicators boost goal score
    future_indicators = ['will', 'going to', 'gonna', 'planning', 'want to', 'need to', 'would like']
    for future in future_indicators:
        if future in text_lower:
            goal_score += 2
    
    # ===== INCOME DETECTION =====
    income_strong_indicators = [
        'got paid', 'received salary', 'received payment', 'got my salary',
        'income', 'earned', 'credited', 'bonus received', 'got bonus','recieve','received',
        'deposited to my', 'transferred to me', 'money came',
        'paycheck', 'dividend', 'refund received', 'cashback',
    ]
    
    for indicator in income_strong_indicators:
        if indicator in text_lower:
            income_score += 10
    
    for keyword in INCOME_KEYWORDS:
        if keyword in text_lower:
            income_score += 3
    
    # ===== EXPENSE DETECTION =====
    expense_strong_indicators = [
        'spent', 'spend', 'paid for', 'paid', 'bought', 'purchased',
        'cost me', 'charged', 'billed', 'expense', 'used for',
    ]
    
    for indicator in expense_strong_indicators:
        if indicator in text_lower:
            expense_score += 10
    
    for keyword in EXPENSE_KEYWORDS:
        if keyword in text_lower:
            expense_score += 3
    
    # ===== DISAMBIGUATION RULES =====
    
    # If both goal and contribution scored, use specific patterns to decide
    if contribution_score > 0 and goal_score > 0:
        # "add to my laptop goal" = contribution
        if re.search(r'(add|put|contribute|deposit)\s+(to|towards|into)\s+(my\s+)?(\w+\s+)?(goal|fund)', text_lower):
            contribution_score += 20
        # "I want to buy laptop" = goal (even if "laptop" matches)
        if re.search(r'(want|wanna|gonna|going|planning|need)\s+to\s+(buy|get|save|purchase)', text_lower):
            goal_score += 20
        # "create goal for laptop" = goal
        if re.search(r'(create|new|set|start|make)\s+(a\s+)?(goal|target|fund)', text_lower):
            goal_score += 20
    
    # Determine winner based on scores
    scores = {
        'contribution': contribution_score,
        'goal': goal_score,
        'income': income_score,
        'expense': expense_score
    }
    
    max_score = max(scores.values())
    
    # If no strong signals, default to expense
    if max_score == 0:
        return 'expense'
    
    # Return the intent with highest score
    # In case of tie, priority: contribution > goal > income > expense
    if contribution_score == max_score:
        return 'contribution'
    elif goal_score == max_score:
        return 'goal'
    elif income_score == max_score:
        return 'income'
    else:
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
        # Tech
        'laptop': 'Buy Laptop',
        'macbook': 'Buy MacBook',
        'computer': 'Buy Computer',
        'pc': 'Buy PC',
        'phone': 'Buy Phone',
        'iphone': 'Buy iPhone',
        'smartphone': 'Buy Smartphone',
        'tablet': 'Buy Tablet',
        'ipad': 'Buy iPad',
        'camera': 'Buy Camera',
        'tv': 'Buy TV',
        'television': 'Buy Television',
        'monitor': 'Buy Monitor',
        'headphones': 'Buy Headphones',
        'airpods': 'Buy AirPods',
        # Gaming
        'playstation': 'Buy PlayStation',
        'ps5': 'Buy PS5',
        'xbox': 'Buy Xbox',
        'nintendo': 'Buy Nintendo',
        'gaming': 'Gaming Setup',
        # Vehicles
        'car': 'Buy Car',
        'bike': 'Buy Bike',
        'motorcycle': 'Buy Motorcycle',
        'scooter': 'Buy Scooter',
        'vehicle': 'Buy Vehicle',
        # Travel
        'vacation': 'Vacation Fund',
        'holiday': 'Holiday Fund',
        'trip': 'Trip Fund',
        'travel': 'Travel Fund',
        'tour': 'Tour Fund',
        'honeymoon': 'Honeymoon Fund',
        # Life Events
        'wedding': 'Wedding Fund',
        'marriage': 'Marriage Fund',
        'birthday': 'Birthday Fund',
        # Property
        'house': 'House Fund',
        'home': 'Home Fund',
        'apartment': 'Apartment Fund',
        'flat': 'Flat Fund',
        'property': 'Property Fund',
        'down payment': 'Down Payment Fund',
        # Education
        'education': 'Education Fund',
        'course': 'Course Fee',
        'college': 'College Fund',
        'university': 'University Fund',
        'degree': 'Degree Fund',
        'masters': 'Masters Fund',
        'mba': 'MBA Fund',
        # Financial
        'emergency': 'Emergency Fund',
        'savings': 'Savings Fund',
        'retirement': 'Retirement Fund',
        'investment': 'Investment Fund',
        # Accessories
        'watch': 'Buy Watch',
        'jewelry': 'Buy Jewelry',
        'ring': 'Buy Ring',
        'furniture': 'Buy Furniture',
        'appliance': 'Buy Appliance',
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
    - "Add money to my emergency fund" -> "emergency"
    """
    text_lower = text.lower()
    
    # Extended patterns to extract goal name from contribution (ordered by specificity)
    patterns = [
        # "contribute/add/put X to my laptop goal"
        r'(?:contribute|add|put|deposit|allocate|transfer|save)\s+(?:\d+\s+)?(?:to|towards|into)\s+(?:my\s+)?(?:the\s+)?(.+?)(?:\s+goal|\s+fund|\s+target)',
        # "contribute/add/put X to laptop" (no goal/fund suffix)
        r'(?:contribute|add|put|deposit|allocate|transfer)\s+(?:\d+\s+)?(?:to|towards|into)\s+(?:my\s+)?(?:the\s+)?([a-zA-Z]+)',
        # "to my laptop goal"
        r'(?:to|towards|into)\s+(?:my\s+)?(?:the\s+)?(.+?)(?:\s+goal|\s+fund|\s+target)',
        # "fund my laptop"
        r'(?:fund|funding)\s+(?:my\s+)?(?:the\s+)?(.+?)(?:\s+goal|\s*$)',
        # "top up my laptop goal"
        r'(?:top\s*up)\s+(?:my\s+)?(?:the\s+)?(.+?)(?:\s+goal|\s+fund|\s*$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            goal_name = match.group(1).strip()
            goal_name = re.sub(r'\s+', ' ', goal_name)
            goal_name = goal_name.strip('.,!? ')
            # Filter out noise words
            noise_words = ['a', 'an', 'the', 'my', 'some', 'more', 'money', 'funds', 'amount']
            if goal_name and goal_name.lower() not in noise_words and len(goal_name) > 1:
                return goal_name.lower()
    
    # Fallback: look for common goal item names with priority
    goal_items_priority = [
        # Tech items
        'laptop', 'macbook', 'iphone', 'phone', 'computer', 'pc', 'tablet', 'ipad',
        'playstation', 'xbox', 'gaming', 'camera', 'tv', 'monitor',
        # Vehicles
        'car', 'bike', 'motorcycle', 'scooter', 'vehicle',
        # Life events
        'wedding', 'marriage', 'honeymoon',
        # Travel
        'vacation', 'holiday', 'trip', 'travel', 'tour',
        # Property
        'house', 'home', 'apartment', 'flat', 'property',
        # Education
        'education', 'course', 'degree', 'college', 'university',
        # Emergency/General
        'emergency', 'savings', 'retirement', 'investment',
        # Accessories
        'watch', 'jewelry', 'ring',
    ]
    
    for item in goal_items_priority:
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
    
    # Look for specific items mentioned (comprehensive list)
    specific_items = {
        # Food & Drinks
        'pizza': 'Pizza',
        'burger': 'Burger',
        'coffee': 'Coffee',
        'tea': 'Tea',
        'lunch': 'Lunch',
        'dinner': 'Dinner',
        'breakfast': 'Breakfast',
        'brunch': 'Brunch',
        'snack': 'Snacks',
        'biryani': 'Biryani',
        'pasta': 'Pasta',
        'sushi': 'Sushi',
        'sandwich': 'Sandwich',
        'salad': 'Salad',
        'dessert': 'Dessert',
        'ice cream': 'Ice Cream',
        'juice': 'Juice',
        'smoothie': 'Smoothie',
        # Food Delivery/Restaurants
        'zomato': 'Zomato Order',
        'swiggy': 'Swiggy Order',
        'doordash': 'DoorDash Order',
        'ubereats': 'Uber Eats Order',
        'mcdonalds': 'McDonalds',
        'kfc': 'KFC',
        'dominos': 'Dominos Pizza',
        'subway': 'Subway',
        'starbucks': 'Starbucks',
        # Transport
        'uber': 'Uber Ride',
        'ola': 'Ola Ride',
        'lyft': 'Lyft Ride',
        'taxi': 'Taxi Ride',
        'cab': 'Cab Ride',
        'rapido': 'Rapido Ride',
        'auto': 'Auto Rickshaw',
        'rickshaw': 'Rickshaw',
        'metro': 'Metro Ticket',
        'bus': 'Bus Fare',
        'train': 'Train Ticket',
        'flight': 'Flight Ticket',
        'petrol': 'Petrol/Fuel',
        'diesel': 'Diesel/Fuel',
        'gas': 'Gas/Fuel',
        'parking': 'Parking Fee',
        'toll': 'Toll Fee',
        # Shopping
        'amazon': 'Amazon Order',
        'flipkart': 'Flipkart Order',
        'myntra': 'Myntra Order',
        'grocery': 'Groceries',
        'groceries': 'Groceries',
        'shopping': 'Shopping',
        'clothes': 'Clothes',
        'shoes': 'Shoes',
        # Entertainment & Subscriptions
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'youtube': 'YouTube Premium',
        'prime': 'Amazon Prime',
        'disney': 'Disney+',
        'hbo': 'HBO',
        'hulu': 'Hulu',
        'movie': 'Movie Ticket',
        'cinema': 'Cinema',
        'concert': 'Concert Ticket',
        'event': 'Event Ticket',
        # Bills & Utilities
        'electricity': 'Electricity Bill',
        'water': 'Water Bill',
        'internet': 'Internet Bill',
        'wifi': 'WiFi Bill',
        'rent': 'Rent Payment',
        'phone': 'Phone Bill',
        'mobile': 'Mobile Bill',
        'recharge': 'Mobile Recharge',
        'insurance': 'Insurance',
        'emi': 'EMI Payment',
        'loan': 'Loan Payment',
        # Health
        'gym': 'Gym Membership',
        'medicine': 'Medicine',
        'pharmacy': 'Pharmacy',
        'doctor': 'Doctor Visit',
        'hospital': 'Hospital',
        'clinic': 'Clinic',
        'checkup': 'Health Checkup',
        'dentist': 'Dentist',
        'therapy': 'Therapy',
        # Personal Care
        'haircut': 'Haircut',
        'salon': 'Salon',
        'spa': 'Spa',
        'grooming': 'Grooming',
        # Education
        'course': 'Course Fee',
        'tuition': 'Tuition Fee',
        'books': 'Books',
        'udemy': 'Udemy Course',
        'coursera': 'Coursera Course',
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
