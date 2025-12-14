from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from math import ceil

from app.models import Income, Goal, GoalStatus, GoalContribution


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


def get_goal_contributions(db: Session, goal_id: int) -> Decimal:
    """
    Get total contributions for a specific goal.
    This is the REAL amount saved, not a projection.
    """
    result = db.query(func.sum(GoalContribution.amount)).filter(
        GoalContribution.goal_id == goal_id
    ).scalar()
    
    return Decimal(result) if result else Decimal("0.00")


def get_all_contributions(db: Session, user_id: int) -> Decimal:
    """
    Get total contributions across all goals for a user.
    """
    result = db.query(func.sum(GoalContribution.amount)).filter(
        GoalContribution.user_id == user_id
    ).scalar()
    
    return Decimal(result) if result else Decimal("0.00")


def calculate_goal_progress(
    db: Session,
    goal: Goal,
    monthly_income: Decimal,
    active_goals_count: int
) -> dict:
    """
    Calculate progress for a single goal using REAL contributions.
    
    Logic:
    1. total_contributed = SUM of actual contributions (REAL!)
    2. suggested_monthly = (monthly_income × savings_rate) ÷ active_goals
    3. remaining = target - contributed
    4. progress = (contributed ÷ target) × 100
    5. months_needed = remaining ÷ suggested_monthly
    """
    now = datetime.utcnow()
    
    # Get REAL contributions
    total_contributed = get_goal_contributions(db, goal.id)
    
    # Handle edge case: no income (can't suggest monthly contribution)
    if monthly_income <= 0:
        remaining = goal.target_amount - total_contributed
        progress = (total_contributed / goal.target_amount) * 100 if goal.target_amount > 0 else Decimal("0.00")
        
        return {
            "monthly_income": Decimal("0.00"),
            "suggested_monthly_contribution": Decimal("0.00"),
            "total_contributed": round(total_contributed, 2),
            "remaining_amount": round(remaining, 2),
            "months_needed": 0,
            "estimated_completion_date": None,
            "progress_percentage": round(progress, 2),
            "is_achievable": False
        }
    
    # Handle edge case: no active goals
    if active_goals_count <= 0:
        active_goals_count = 1
    
    # Calculate suggested monthly contribution
    savings_rate = Decimal(str(goal.savings_rate))
    total_savings_pool = monthly_income * savings_rate
    suggested_monthly = total_savings_pool / active_goals_count
    
    # Calculate remaining amount
    remaining_amount = goal.target_amount - total_contributed
    if remaining_amount < 0:
        remaining_amount = Decimal("0.00")
    
    # Calculate progress percentage
    progress_percentage = (total_contributed / goal.target_amount) * 100 if goal.target_amount > 0 else Decimal("0.00")
    
    # Calculate months needed to complete
    if suggested_monthly > 0 and remaining_amount > 0:
        months_needed = ceil(float(remaining_amount / suggested_monthly))
        estimated_completion_date = now + relativedelta(months=months_needed)
    elif remaining_amount <= 0:
        months_needed = 0
        estimated_completion_date = now  # Goal achieved!
    else:
        months_needed = 0
        estimated_completion_date = None
    
    return {
        "monthly_income": monthly_income,
        "suggested_monthly_contribution": round(suggested_monthly, 2),
        "total_contributed": round(total_contributed, 2),
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
    
    progress = calculate_goal_progress(db, goal, monthly_income, active_goals_count)
    
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
    total_contributed_all = Decimal("0.00")
    
    for goal in goals:
        progress = calculate_goal_progress(db, goal, monthly_income, active_goals_count)
        total_contributed_all += progress["total_contributed"]
        
        goals_with_progress.append({
            "id": goal.id,
            "title": goal.title,
            "target_amount": goal.target_amount,
            "savings_rate": goal.savings_rate,
            "status": goal.status.value,
            "created_at": goal.created_at,
            **progress
        })
    
    # Calculate total savings pool (using default 20%)
    default_rate = Decimal("0.20")
    if goals:
        default_rate = Decimal(str(goals[0].savings_rate))
    total_savings_pool = monthly_income * default_rate
    
    return {
        "monthly_income": monthly_income,
        "total_savings_pool": round(total_savings_pool, 2),
        "active_goals_count": active_goals_count,
        "total_contributed_all_goals": round(total_contributed_all, 2),
        "goals": goals_with_progress
    }


def check_and_complete_goal(db: Session, goal: Goal) -> bool:
    """
    Check if goal has reached target and auto-complete if so.
    Returns True if goal was completed.
    """
    total_contributed = get_goal_contributions(db, goal.id)
    
    if total_contributed >= goal.target_amount and goal.status == GoalStatus.active:
        goal.status = GoalStatus.completed
        db.commit()
        return True
    
    return False
