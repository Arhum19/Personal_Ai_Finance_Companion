from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.dependencies import get_db, get_current_user
from app.models import User, Income, Expense, GoalContribution
from app.schemas import BalanceResponse

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get financial balance summary for the logged-in user.
    
    Returns:
    - total_income: All income ever recorded
    - total_expense: All expenses ever recorded
    - goal_contributions: Total contributed to goals (reserved money)
    - remaining_balance: income - expense (what's left after spending)
    - available_to_spend: remaining_balance - goal_contributions (what you can actually use)
    """
    # Calculate total income
    income_result = db.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(Income.user_id == current_user.id).scalar()
    
    # Calculate total expenses
    expense_result = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.user_id == current_user.id).scalar()
    
    # Calculate total goal contributions
    contribution_result = db.query(
        func.coalesce(func.sum(GoalContribution.amount), 0)
    ).filter(GoalContribution.user_id == current_user.id).scalar()
    
    total_income = Decimal(income_result) if income_result else Decimal("0")
    total_expense = Decimal(expense_result) if expense_result else Decimal("0")
    goal_contributions = Decimal(contribution_result) if contribution_result else Decimal("0")
    
    remaining_balance = total_income - total_expense
    available_to_spend = remaining_balance - goal_contributions
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "goal_contributions": goal_contributions,
        "remaining_balance": remaining_balance,
        "available_to_spend": available_to_spend
    }
