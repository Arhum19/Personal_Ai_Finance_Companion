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
    'food': ['lunch', 'dinner', 'breakfast', 'coffee', 'meal', 'food', 'eat', 'brunch', 'restaurant', 'pizza', 'burger'],
    'transport': ['transport', 'taxi', 'uber', 'bus', 'train', 'petrol', 'gas', 'fuel', 'ride', 'metro', 'cab', 'ola'],
    'shopping': ['shopping', 'clothes', 'shoes', 'grocery', 'groceries', 'market', 'store', 'mall', 'amazon', 'online'],
    'entertainment': ['movie', 'cinema', 'netflix', 'game', 'gaming', 'concert', 'club', 'party', 'spotify'],
    'bills': ['bill', 'electricity', 'water', 'internet', 'phone', 'rent', 'wifi', 'mobile', 'recharge'],
    'health': ['doctor', 'medicine', 'pharmacy', 'gym', 'hospital', 'medical', 'health', 'fitness'],
    'other': ['gift', 'donation', 'misc', 'other']
}

# Income detection keywords
INCOME_KEYWORDS = [
    'got paid', 'received', 'income', 'salary', 'earned', 'credited', 
    'bonus', 'payment received', 'got my', 'deposited', 'transferred to me',
    'freelance payment', 'client paid', 'refund'
]

# Income source keywords
INCOME_SOURCES = {
    'salary': ['salary', 'paycheck', 'monthly pay', 'wages'],
    'freelance': ['freelance', 'client', 'project', 'gig', 'contract'],
    'bonus': ['bonus', 'incentive', 'reward'],
    'refund': ['refund', 'cashback', 'returned'],
    'gift': ['gift', 'birthday', 'present'],
    'investment': ['dividend', 'interest', 'investment', 'returns'],
    'other': ['other', 'misc']
}

# Goal detection keywords - these trigger goal creation
GOAL_KEYWORDS = [
    'goal', 'want to', 'save for', 'saving for', 'planning to buy',
    'want a', 'need to save', 'target', 'aim to', 'wish to',
    'dream of', 'looking to buy', 'gonna buy', 'going to buy',
    'save up for', 'saving up', 'fund for', 'budget for'
]

# Number words for conversion
NUMBER_WORDS = set("""
zero one two three four five six seven eight nine ten eleven twelve thirteen 
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty 
sixty seventy eighty ninety hundred thousand lakh million crore
""".split())
