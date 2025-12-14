"""
API Client for Voice Client
Handles authentication and API calls to FastAPI backend
"""
import os
import json
import requests
from typing import Optional
from getpass import getpass

from .config import API_BASE_URL, TOKEN_FILE


class FinanceAPIClient:
    """
    HTTP client for Finance Companion API.
    Handles authentication, token management, and API calls.
    """
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token: Optional[str] = None
        self.categories_cache: dict = {}  # name -> id mapping
        self._load_token()
    
    # ==================== TOKEN MANAGEMENT ====================
    
    def _load_token(self):
        """Load token from file if exists."""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    print(f"✅ Loaded saved token")
            except Exception as e:
                print(f"⚠️ Could not load saved token: {e}")
    
    def _save_token(self, token: str):
        """Save token to file."""
        try:
            with open(TOKEN_FILE, 'w') as f:
                json.dump({'token': token}, f)
            print(f"✅ Token saved for future sessions")
        except Exception as e:
            print(f"⚠️ Could not save token: {e}")
    
    def _clear_token(self):
        """Clear saved token."""
        self.token = None
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
    
    def _get_headers(self) -> dict:
        """Get headers with authorization."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    # ==================== AUTHENTICATION ====================
    
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Login to get JWT token.
        If email/password not provided, prompts user.
        """
        if not email:
            email = input("📧 Email: ").strip()
        if not password:
            password = getpass("🔒 Password: ")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self._save_token(self.token)
                print(f"✅ Logged in as: {data['user']['name']} ({data['user']['email']})")
                return True
            else:
                error = response.json().get("detail", "Login failed")
                print(f"❌ Login failed: {error}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to API at {self.base_url}")
            print("   Make sure the FastAPI server is running: uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def logout(self):
        """Clear token and logout."""
        self._clear_token()
        self.categories_cache = {}
        print("👋 Logged out successfully")
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        if not self.token:
            return False
        
        # Verify token by calling /auth/me
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except:
            return False
    
    def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated, prompt login if not."""
        if self.is_authenticated():
            return True
        
        print("\n🔐 Authentication required")
        return self.login()
    
    # ==================== CATEGORIES ====================
    
    def fetch_categories(self) -> dict:
        """
        Fetch user's categories and cache them.
        Returns dict mapping category name (lowercase) to id.
        """
        if not self.token:
            print("❌ Not authenticated")
            return {}
        
        try:
            response = requests.get(
                f"{self.base_url}/category/",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                categories = response.json()
                self.categories_cache = {
                    cat["name"].lower(): cat["id"] 
                    for cat in categories
                }
                print(f"📂 Loaded {len(categories)} categories")
                return self.categories_cache
            elif response.status_code == 401:
                print("❌ Token expired. Please login again.")
                self._clear_token()
                return {}
            else:
                print(f"❌ Failed to fetch categories: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching categories: {e}")
            return {}
    
    def get_category_id(self, category_name: str) -> Optional[int]:
        """Get category ID from name."""
        if not self.categories_cache:
            self.fetch_categories()
        
        return self.categories_cache.get(category_name.lower())
    
    # ==================== EXPENSE API ====================
    
    def post_expense(self, data: dict) -> dict:
        """
        Create a new expense.
        
        Args:
            data: dict with title, amount, description, category (name), date
            
        Returns:
            API response dict or error dict
        """
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        # Get category ID
        category_name = data.get("category", "other")
        category_id = self.get_category_id(category_name)
        
        if not category_id:
            # Try to create the category
            print(f"⚠️ Category '{category_name}' not found. Using 'Other'.")
            category_id = self.get_category_id("other")
            
            if not category_id:
                return {"error": f"Category '{category_name}' not found and 'Other' doesn't exist"}
        
        # Prepare payload
        payload = {
            "title": data.get("title", "Expense"),
            "amount": data.get("amount"),
            "description": data.get("description", ""),
            "category_id": category_id,
            "date": data.get("date")
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/expense/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                print("✅ Expense created successfully!")
                return response.json()
            elif response.status_code == 401:
                print("❌ Token expired. Please login again.")
                self._clear_token()
                return {"error": "Token expired"}
            else:
                error = response.json().get("detail", response.text)
                print(f"❌ Failed to create expense: {error}")
                return {"error": error}
                
        except Exception as e:
            print(f"❌ Error creating expense: {e}")
            return {"error": str(e)}
    
    # ==================== INCOME API ====================
    
    def post_income(self, data: dict) -> dict:
        """
        Create a new income.
        
        Args:
            data: dict with amount, source, date
            
        Returns:
            API response dict or error dict
        """
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        # Prepare payload
        payload = {
            "amount": data.get("amount"),
            "source": data.get("source", "Other"),
            "date": data.get("date")
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/income/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                print("✅ Income created successfully!")
                return response.json()
            elif response.status_code == 401:
                print("❌ Token expired. Please login again.")
                self._clear_token()
                return {"error": "Token expired"}
            else:
                error = response.json().get("detail", response.text)
                print(f"❌ Failed to create income: {error}")
                return {"error": error}
                
        except Exception as e:
            print(f"❌ Error creating income: {e}")
            return {"error": str(e)}
    
    # ==================== BALANCE/SUMMARY ====================
    
    def get_balance(self) -> dict:
        """Get current balance summary."""
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        try:
            response = requests.get(
                f"{self.base_url}/summary/balance",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Failed to fetch balance"}
                
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== GOALS API ====================
    
    def post_goal(self, data: dict) -> dict:
        """
        Create a new goal.
        
        Args:
            data: dict with title, target_amount (amount), savings_rate (optional)
            
        Returns:
            API response dict with calculated timeline or error dict
        """
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        # Prepare payload
        payload = {
            "title": data.get("title", "Savings Goal"),
            "target_amount": data.get("amount"),
            "savings_rate": data.get("savings_rate", 0.20)  # Default 20%
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/goals/",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                print("✅ Goal created successfully!")
                return response.json()
            elif response.status_code == 401:
                print("❌ Token expired. Please login again.")
                self._clear_token()
                return {"error": "Token expired"}
            else:
                error = response.json().get("detail", response.text)
                print(f"❌ Failed to create goal: {error}")
                return {"error": error}
                
        except Exception as e:
            print(f"❌ Error creating goal: {e}")
            return {"error": str(e)}
    
    def get_goals(self, include_inactive: bool = False) -> dict:
        """
        Get all goals with progress calculations.
        
        Args:
            include_inactive: Include completed/paused goals
            
        Returns:
            API response with goals list and progress data
        """
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        try:
            response = requests.get(
                f"{self.base_url}/goals/",
                params={"include_inactive": include_inactive},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Failed to fetch goals"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_goal_id_by_name(self, goal_name: str) -> Optional[int]:
        """
        Find a goal ID by searching for a matching name.
        
        Args:
            goal_name: Partial or full goal name (case-insensitive)
            
        Returns:
            Goal ID if found, None otherwise
        """
        goals_data = self.get_goals()
        if goals_data.get("error"):
            return None
        
        goals = goals_data.get("goals", [])
        goal_name_lower = goal_name.lower()
        
        # Try exact match first
        for goal in goals:
            if goal_name_lower == goal["title"].lower():
                return goal["id"]
        
        # Try partial match
        for goal in goals:
            if goal_name_lower in goal["title"].lower():
                return goal["id"]
        
        return None
    
    def contribute_to_goal(self, goal_id: int, amount: float) -> dict:
        """
        Add a contribution to a goal.
        
        Args:
            goal_id: ID of the goal to contribute to
            amount: Amount to contribute
            
        Returns:
            API response with updated goal progress or error dict
        """
        if not self.ensure_authenticated():
            return {"error": "Not authenticated"}
        
        payload = {
            "amount": amount
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/goals/{goal_id}/contribute",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                print("✅ Contribution added successfully!")
                return response.json()
            elif response.status_code == 401:
                print("❌ Token expired. Please login again.")
                self._clear_token()
                return {"error": "Token expired"}
            elif response.status_code == 404:
                return {"error": "Goal not found"}
            else:
                error = response.json().get("detail", response.text)
                print(f"❌ Failed to add contribution: {error}")
                return {"error": error}
                
        except Exception as e:
            print(f"❌ Error adding contribution: {e}")
            return {"error": str(e)}


# Singleton instance
_client = None

def get_client() -> FinanceAPIClient:
    """Get singleton API client instance."""
    global _client
    if _client is None:
        _client = FinanceAPIClient()
    return _client


# Quick test
if __name__ == "__main__":
    print("=" * 60)
    print("API Client Test")
    print("=" * 60)
    
    client = get_client()
    
    # Test login
    if client.ensure_authenticated():
        print("\n📂 Fetching categories...")
        categories = client.fetch_categories()
        print(f"Categories: {list(categories.keys())}")
        
        print("\n💰 Fetching balance...")
        balance = client.get_balance()
        print(f"Balance: {balance}")
