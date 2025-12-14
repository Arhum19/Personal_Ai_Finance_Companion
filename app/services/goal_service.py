from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from math import ceil

from app.models import Income, Goal, GoalStatus


def get_current_month_income(db: Session, user_id: int) -> Decimal:
    """
    Get total income for the current month only.
    Returns 0 if no income found.
    """
    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month
    
    result = db.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        extract('year', Income.date) == current_year,
        extract('month', Income.date) == current_month
    ).scalar()
    
    return Decimal(result) if result else Decimal("0.00")


def get_active_goals_count(db: Session, user_id: int) -> int:
    """Count active goals for the user."""
    return db.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.status == GoalStatus.active
    ).count()


def calculate_goal_progress(
    goal: Goal,
    monthly_income: Decimal,
    active_goals_count: int
) -> dict:
    """
    Calculate progress for a single goal.
    
    Logic:
    1. total_savings_pool = monthly_income × savings_rate
    2. your_monthly_allocation = total_savings_pool ÷ active_goals_count
    3. months_elapsed = (today - created_at) in months
    4. amount_saved = months_elapsed × monthly_allocation
    5. progress_percentage = (amount_saved ÷ target_amount) × 100
    6. months_needed = (target_amount - amount_saved) ÷ monthly_allocation
    7. estimated_completion = today + months_needed
    """
    now = datetime.utcnow()
    
    # Handle edge case: no income
    if monthly_income <= 0:
        return {
            "monthly_income": Decimal("0.00"),
            "total_savings_pool": Decimal("0.00"),
            "active_goals_count": active_goals_count,
            "your_monthly_allocation": Decimal("0.00"),
            "months_elapsed": 0,
            "amount_saved_so_far": Decimal("0.00"),
            "remaining_amount": goal.target_amount,
            "months_needed": 0,
            "estimated_completion_date": None,
            "progress_percentage": Decimal("0.00"),
            "is_achievable": False
        }
    
    # Handle edge case: no active goals (shouldn't happen, but safety)
    if active_goals_count <= 0:
        active_goals_count = 1
    
    # Calculate savings pool
    savings_rate = Decimal(str(goal.savings_rate))
    total_savings_pool = monthly_income * savings_rate
    your_monthly_allocation = total_savings_pool / active_goals_count
    
    # Calculate months elapsed since goal creation
    # Using relativedelta for accurate month calculation
    created_date = goal.created_at
    delta = relativedelta(now, created_date)
    months_elapsed = delta.years * 12 + delta.months
    
    # If less than a month has passed, consider partial month
    # For simplicity, we'll start counting from month 0
    # The first full month of saving starts after creation
    
    # Calculate amount saved so far
    amount_saved_so_far = your_monthly_allocation * months_elapsed
    
    # Cap at target amount (can't save more than target)
    if amount_saved_so_far > goal.target_amount:
        amount_saved_so_far = goal.target_amount
    
    remaining_amount = goal.target_amount - amount_saved_so_far
    
    # Calculate progress percentage
    progress_percentage = (amount_saved_so_far / goal.target_amount) * 100
    
    # Calculate months needed to complete (from now)
    if your_monthly_allocation > 0 and remaining_amount > 0:
        months_needed = ceil(float(remaining_amount / your_monthly_allocation))
        estimated_completion_date = now + relativedelta(months=months_needed)
    elif remaining_amount <= 0:
        months_needed = 0
        estimated_completion_date = now  # Already achieved!
    else:
        months_needed = 0
        estimated_completion_date = None
    
    return {
        "monthly_income": monthly_income,
        "total_savings_pool": round(total_savings_pool, 2),
        "active_goals_count": active_goals_count,
        "your_monthly_allocation": round(your_monthly_allocation, 2),
        "months_elapsed": months_elapsed,
        "amount_saved_so_far": round(amount_saved_so_far, 2),
        "remaining_amount": round(remaining_amount, 2),
        "months_needed": months_needed,
        "estimated_completion_date": estimated_completion_date,
        "progress_percentage": round(progress_percentage, 2),
        "is_achievable": True
    }


def get_goal_with_progress(db: Session, goal: Goal, user_id: int) -> dict:
    """
    Get a single goal with all calculated progress fields.
    """
    monthly_income = get_current_month_income(db, user_id)
    active_goals_count = get_active_goals_count(db, user_id)
    
    progress = calculate_goal_progress(goal, monthly_income, active_goals_count)
    
    return {
        "id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "savings_rate": goal.savings_rate,
        "status": goal.status.value,
        "created_at": goal.created_at,
        **progress
    }


def get_all_goals_with_progress(db: Session, user_id: int, include_inactive: bool = False) -> dict:
    """
    Get all goals with progress calculations.
    By default, only returns active goals. Set include_inactive=True for all.
    """
    # Get income and count ONCE for efficiency
    monthly_income = get_current_month_income(db, user_id)
    active_goals_count = get_active_goals_count(db, user_id)
    
    # Query goals
    query = db.query(Goal).filter(Goal.user_id == user_id)
    if not include_inactive:
        query = query.filter(Goal.status == GoalStatus.active)
    
    goals = query.order_by(Goal.created_at.desc()).all()
    
    # Calculate progress for each goal
    goals_with_progress = []
    for goal in goals:
        progress = calculate_goal_progress(goal, monthly_income, active_goals_count)
        goals_with_progress.append({
            "id": goal.id,
            "title": goal.title,
            "target_amount": goal.target_amount,
            "savings_rate": goal.savings_rate,
            "status": goal.status.value,
            "created_at": goal.created_at,
            **progress
        })
    
    # Calculate total savings pool (using first goal's rate, or default 20%)
    default_rate = Decimal("0.20")
    if goals:
        default_rate = Decimal(str(goals[0].savings_rate))
    total_savings_pool = monthly_income * default_rate
    
    return {
        "monthly_income": monthly_income,
        "total_savings_pool": round(total_savings_pool, 2),
        "active_goals_count": active_goals_count,
        "goals": goals_with_progress
    }
