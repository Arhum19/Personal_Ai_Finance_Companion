from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.dependencies import get_db, get_current_user
from app.models import User, Income, Expense
from app.schemas import BalanceResponse

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get financial balance summary for the logged-in user.
    Returns total income, total expenses, and remaining balance.
    """
    # Calculate total income
    income_result = db.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(Income.user_id == current_user.id).scalar()
    
    # Calculate total expenses
    expense_result = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.user_id == current_user.id).scalar()
    
    total_income = Decimal(income_result) if income_result else Decimal("0")
    total_expense = Decimal(expense_result) if expense_result else Decimal("0")
    remaining_balance = total_income - total_expense
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "remaining_balance": remaining_balance
    }
