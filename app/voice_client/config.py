"""
Configuration for Voice Client
"""
import os

# API Configuration
API_BASE_URL = os.getenv("FINANCE_API_URL", "http://127.0.0.1:8000")

# Whisper Configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")  # tiny, base, small, medium, large

# Audio Configuration
SAMPLE_RATE = 16000
CHANNELS = 1

# Token storage path (in user's home directory)
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".finance_companion_token")

# Default categories (must match what's seeded in DB)
DEFAULT_CATEGORIES = {
    'food': [
        'lunch', 'dinner', 'breakfast', 'coffee', 'meal', 'food', 'eat', 'brunch', 
        'restaurant', 'pizza', 'burger', 'snack', 'takeout', 'delivery', 'zomato', 
        'swiggy', 'doordash', 'ubereats', 'grubhub', 'tea', 'juice', 'drink', 
        'sandwich', 'salad', 'biryani', 'noodles', 'pasta', 'sushi', 'thali',
        'cafe', 'starbucks', 'mcdonalds', 'kfc', 'dominos', 'subway'
    ],
    'transport': [
        'transport', 'taxi', 'uber', 'bus', 'train', 'petrol', 'gas', 'fuel', 
        'ride', 'metro', 'cab', 'ola', 'lyft', 'rapido', 'auto', 'rickshaw',
        'parking', 'toll', 'flight', 'airplane', 'airport', 'commute', 'travel',
        'bike', 'scooter', 'car service', 'vehicle', 'diesel'
    ],
    'shopping': [
        'shopping', 'clothes', 'shoes', 'grocery', 'groceries', 'market', 'store', 
        'mall', 'amazon', 'online', 'flipkart', 'myntra', 'ajio', 'walmart',
        'target', 'costco', 'purchase', 'bought', 'order', 'ordered', 'delivery',
        'electronics', 'gadget', 'accessory', 'fashion', 'dress', 'shirt', 'pants'
    ],
    'entertainment': [
        'movie', 'cinema', 'netflix', 'game', 'gaming', 'concert', 'club', 'party', 
        'spotify', 'youtube', 'prime', 'disney', 'hbo', 'hulu', 'theatre', 'show',
        'subscription', 'streaming', 'music', 'event', 'ticket', 'festival', 'fun',
        'outing', 'hangout', 'bar', 'pub', 'lounge', 'playstation', 'xbox', 'steam'
    ],
    'bills': [
        'bill', 'electricity', 'water', 'internet', 'phone', 'rent', 'wifi', 
        'mobile', 'recharge', 'utility', 'utilities', 'insurance', 'emi', 'loan',
        'mortgage', 'broadband', 'cable', 'maintenance', 'society', 'dues',
        'subscription', 'membership', 'premium', 'installment', 'payment'
    ],
    'health': [
        'doctor', 'medicine', 'pharmacy', 'gym', 'hospital', 'medical', 'health', 
        'fitness', 'clinic', 'consultation', 'checkup', 'treatment', 'therapy',
        'dentist', 'dental', 'eye', 'vision', 'glasses', 'vitamins', 'supplements',
        'lab', 'test', 'scan', 'xray', 'surgery', 'operation', 'wellness'
    ],
    'education': [
        'course', 'class', 'tuition', 'school', 'college', 'university', 'books',
        'study', 'learning', 'tutorial', 'udemy', 'coursera', 'skillshare', 
        'certification', 'exam', 'training', 'workshop', 'seminar', 'coaching'
    ],
    'personal': [
        'haircut', 'salon', 'spa', 'grooming', 'beauty', 'skincare', 'cosmetic',
        'personal care', 'self care', 'massage', 'parlor', 'barber'
    ],
    'other': ['gift', 'donation', 'misc', 'other', 'miscellaneous', 'random']
}

# Income detection keywords - EXPANDED
INCOME_KEYWORDS = [
    # Direct income phrases
    'got paid', 'received', 'income', 'salary', 'earned', 'credited', 
    'bonus', 'payment received', 'got my', 'deposited', 'transferred to me',
    'freelance payment', 'client paid', 'refund', 'got money', 'money came',
    # Salary variations
    'paycheck', 'wages', 'monthly pay', 'pay day', 'payday',
    # Passive income
    'dividend', 'interest earned', 'rental income', 'royalty',
    # Other income
    'cashback', 'reward points', 'won', 'prize', 'lottery',
    'inheritance', 'gift received', 'money from', 'sent me money',
    # Earning phrases
    'made money', 'earned from', 'profit from', 'revenue'
]

# Income source keywords - EXPANDED
INCOME_SOURCES = {
    'salary': ['salary', 'paycheck', 'monthly pay', 'wages', 'pay day', 'payday', 'office', 'company', 'employer'],
    'freelance': ['freelance', 'client', 'project', 'gig', 'contract', 'consulting', 'side job', 'side hustle'],
    'bonus': ['bonus', 'incentive', 'reward', 'performance', 'annual bonus', 'quarterly'],
    'refund': ['refund', 'cashback', 'returned', 'reimbursement', 'claim'],
    'gift': ['gift', 'birthday', 'present', 'wedding', 'received from', 'family', 'parents', 'friend'],
    'investment': ['dividend', 'interest', 'investment', 'returns', 'stock', 'mutual fund', 'fd', 'fixed deposit'],
    'rental': ['rent', 'rental', 'tenant', 'property'],
    'business': ['business', 'sales', 'profit', 'revenue', 'customer'],
    'other': ['other', 'misc', 'miscellaneous', 'rent', 'income']
}

# Goal detection keywords - VERY SPECIFIC for NEW goal creation
# These indicate the user wants to CREATE or SET UP a new savings goal
GOAL_KEYWORDS = [
    # Explicit goal creation
    'create goal', 'new goal', 'set goal', 'make goal', 'start goal',
    'create a goal', 'set a goal', 'make a goal', 'start a goal',
    # Future buying intent (creating goal)
    'want to buy', 'wanna buy', 'gonna buy', 'going to buy', 'planning to buy',
    'want to get', 'wanna get', 'gonna get', 'going to get', 'planning to get',
    'want to purchase', 'planning to purchase',
    # Saving intent (creating goal)  
    'save for', 'saving for', 'save up for', 'saving up for',
    'need to save for', 'want to save for', 'start saving for',
    # Dream/wish (creating goal)
    'dream of buying', 'dream to buy', 'wish to buy', 'hoping to buy',
    'looking to buy', 'thinking of buying', 'plan to buy',
    # Target setting
    'set target', 'my target is', 'target to', 'aim to buy', 'aim for',
    # Goal for specific item
    'goal for', 'goal to buy', 'goal is to', 'goal of buying',
    # Fund creation
    'create fund', 'start fund', 'build fund', 'emergency fund goal',
    # Budget intent
    'budget for', 'budgeting for', 'need budget for'
]

# Contribution detection keywords - VERY SPECIFIC for ADDING to existing goal
# These indicate the user wants to ADD MONEY to an existing goal
CONTRIBUTION_KEYWORDS = [
    # Direct contribution phrases
    'contribute', 'contributing', 'contribution to', 'make contribution',
    # Adding to goal
    'add to goal', 'add to my goal', 'adding to goal', 'add money to goal',
    'add to my', 'adding to my', 'add funds to',
    # Put/deposit towards goal
    'put towards', 'putting towards', 'put into goal', 'put in goal',
    'deposit to goal', 'deposit into goal', 'depositing to goal',
    # Transfer to goal
    'transfer to goal', 'move to goal', 'moving to goal',
    # Allocate to goal  
    'allocate to', 'allocating to', 'allocate for goal',
    # Save to specific goal (not general saving)
    'save to goal', 'saving to goal', 'save into goal',
    # Fund existing goal
    'fund my goal', 'funding my goal', 'fund the goal',
    # Towards existing fund
    'towards my fund', 'to my fund', 'into my fund',
    # Top up goal
    'top up goal', 'top up my', 'topping up',
    # Increase goal
    'increase my goal', 'increase goal savings',
    # Specific contribution patterns
    'contribute to laptop', 'contribute to car', 'contribute to vacation',
    'add to laptop', 'add to car', 'add to vacation', 'add to emergency',
    'put towards laptop', 'put towards car', 'put towards vacation'
]

# Expense detection keywords (to avoid confusion)
EXPENSE_KEYWORDS = [
    'spent', 'spend', 'spending', 'paid', 'pay', 'paying',
    'bought', 'buy', 'buying', 'purchased', 'purchase',
    'cost', 'costed', 'charged', 'charge', 'billed','recieved', 'recieve',
    'expense', 'expensed', 'used', 'consumed'
]

# Number words for conversion
NUMBER_WORDS = set("""
zero one two three four five six seven eight nine ten eleven twelve thirteen 
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty 
sixty seventy eighty ninety hundred thousand lakh million crore billion
""".split())
