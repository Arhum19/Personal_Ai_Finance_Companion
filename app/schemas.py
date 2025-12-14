from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from decimal import Decimal

# ==================== USER SCHEMAS ====================

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., max_length=72, min_length=8)

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel): 
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: str | None = None


# ==================== CATEGORY SCHEMAS ====================

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")

class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")

class CategoryResponse(BaseModel):
    id: int
    name: str
    user_id: int

    class Config:
        from_attributes = True


# ==================== INCOME SCHEMAS ====================

class IncomeCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount must be greater than 0")
    source: str | None = Field(None, max_length=200, description="Income source (optional)")
    date: datetime | None = Field(None, description="Date of income (defaults to now)")

class IncomeUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0, description="Amount must be greater than 0")
    source: str | None = Field(None, max_length=200)
    date: datetime | None = None

class IncomeResponse(BaseModel):
    id: int
    amount: Decimal
    source: str | None
    date: datetime
    user_id: int

    class Config:
        from_attributes = True

class IncomeTotalResponse(BaseModel):
    total_income: Decimal
    count: int


# ==================== EXPENSE SCHEMAS ====================

class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Expense title")
    amount: Decimal = Field(..., gt=0, description="Amount must be greater than 0")
    description: str | None = Field(None, description="Optional description")
    date: datetime | None = Field(None, description="Date of expense (defaults to now)")
    category_id: int = Field(..., description="Category ID (must belong to user)")

class ExpenseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    amount: Decimal | None = Field(None, gt=0)
    description: str | None = None
    date: datetime | None = None
    category_id: int | None = None

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: Decimal
    description: str | None
    date: datetime
    category_id: int
    user_id: int

    class Config:
        from_attributes = True


# ==================== SUMMARY SCHEMAS ====================

class BalanceResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    goal_contributions: Decimal          # Total contributed to goals
    remaining_balance: Decimal           # income - expense
    available_to_spend: Decimal          # remaining_balance - goal_contributions


# ==================== GOAL SCHEMAS ====================

class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Goal title (e.g., 'Buy Laptop')")
    target_amount: Decimal = Field(..., gt=0, description="Target amount to achieve")
    savings_rate: Decimal = Field(default=Decimal("0.20"), ge=0.01, le=1.0, description="Savings rate (default 20%)")

class GoalUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    target_amount: Decimal | None = Field(None, gt=0)
    savings_rate: Decimal | None = Field(None, ge=0.01, le=1.0)
    status: str | None = Field(None, description="Status: active, completed, paused")

class GoalResponse(BaseModel):
    id: int
    title: str
    target_amount: Decimal
    savings_rate: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class GoalProgressResponse(BaseModel):
    """Detailed goal with calculated progress for dashboard/charts"""
    id: int
    title: str
    target_amount: Decimal
    savings_rate: Decimal
    status: str
    created_at: datetime
    
    # Calculated fields for dashboard/charts
    monthly_income: Decimal
    suggested_monthly_contribution: Decimal  # savings_rate × monthly_income ÷ active_goals
    total_contributed: Decimal               # SUM of actual contributions (REAL!)
    remaining_amount: Decimal                # target - contributed
    months_needed: int                       # remaining ÷ suggested_monthly
    estimated_completion_date: datetime | None
    progress_percentage: Decimal             # (contributed ÷ target) × 100
    is_achievable: bool                      # False if no income

    class Config:
        from_attributes = True

class AllGoalsProgressResponse(BaseModel):
    """Summary for all goals - useful for dashboard overview"""
    monthly_income: Decimal
    total_savings_pool: Decimal
    active_goals_count: int
    total_contributed_all_goals: Decimal     # Sum of all contributions
    goals: list[GoalProgressResponse]


# ==================== GOAL CONTRIBUTION SCHEMAS ====================

class GoalContributionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount to contribute")
    date: datetime | None = Field(None, description="Date of contribution (defaults to now)")

class GoalContributionResponse(BaseModel):
    id: int
    amount: Decimal
    date: datetime
    goal_id: int
    user_id: int
    goal_title: str | None = None  # Optionally include goal title

    class Config:
        from_attributes = True

class GoalContributionsListResponse(BaseModel):
    goal_id: int
    goal_title: str
    target_amount: Decimal
    total_contributed: Decimal
    contributions: list[GoalContributionResponse]