from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from datetime import datetime
from decimal import Decimal

from app.dependencies import get_db, get_current_user
from app.models import User, Expense, Category, Income, GoalContribution
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.cache import insight_cache

router = APIRouter(prefix="/expense", tags=["Expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new expense"""
    # Validate: Category exists AND belongs to this user
    category = db.query(Category).filter(
        Category.id == expense.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or doesn't belong to you"
        )
    
    # ===== VALIDATION: Check if user has sufficient income =====
    # Calculate current financial balance
    income_result = db.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(Income.user_id == current_user.id).scalar()
    
    current_expense_result = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.user_id == current_user.id).scalar()
    
    goal_contribution_result = db.query(
        func.coalesce(func.sum(GoalContribution.amount), 0)
    ).filter(GoalContribution.user_id == current_user.id).scalar()
    
    total_income = Decimal(income_result) if income_result else Decimal("0")
    current_expenses = Decimal(current_expense_result) if current_expense_result else Decimal("0")
    goal_contributions = Decimal(goal_contribution_result) if goal_contribution_result else Decimal("0")
    expense_amount = Decimal(str(expense.amount))
    
    # Calculate current available balance
    remaining_balance = total_income - current_expenses
    current_available = remaining_balance - goal_contributions
    
    # FIRST CHECK: If available balance is already zero or negative, reject any expense
    if current_available <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add expense. Your available balance is already insufficient. "
                   f"Total income: ${float(total_income):.2f}. "
                   f"Current expenses: ${float(current_expenses):.2f}. "
                   f"Goal contributions (reserved): ${float(goal_contributions):.2f}. "
                   f"Available to spend: ${float(current_available):.2f}. "
                   f"Please increase your income or reduce goal contributions before adding expenses."
        )
    
    # SECOND CHECK: Calculate what would be the new balance after adding this expense
    new_total_expenses = current_expenses + expense_amount
    remaining_after_expense = total_income - new_total_expenses
    available_after_expense = remaining_after_expense - goal_contributions
    
    # If expense would make balance negative, reject it
    if available_after_expense < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient income to add this expense. "
                   f"Current available balance: ${float(current_available):.2f}. "
                   f"Requested expense: ${float(expense_amount):.2f}. "
                   f"This would result in a negative balance of ${float(available_after_expense):.2f}. "
                   f"Please reduce the expense amount (max: ${float(current_available):.2f}) or add more income."
        )
    
    db_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        description=expense.description,
        date=expense.date or datetime.utcnow(),  # Default to now if not provided
        category_id=expense.category_id,
        user_id=current_user.id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    # Invalidate insights cache so dashboard shows fresh data
    insight_cache.invalidate(current_user.id)
    
    return db_expense


@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all expenses for the logged-in user"""
    expenses = db.query(Expense).options(
        joinedload(Expense.category)
    ).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.date.desc()).offset(skip).limit(limit).all()
    
    # Map to response with category name
    return [ExpenseResponse.from_orm_with_category(exp) for exp in expenses]


@router.get("/category/{category_id}", response_model=List[ExpenseResponse])
def get_expenses_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all expenses for a specific category"""
    # First verify the category exists and belongs to user
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.category_id == category_id
    ).order_by(Expense.date.desc()).offset(skip).limit(limit).all()
    return expenses


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific expense by ID"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an expense"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If updating category, validate it exists and belongs to user
    if expense_update.category_id is not None:
        category = db.query(Category).filter(
            Category.id == expense_update.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or doesn't belong to you"
            )
        expense.category_id = expense_update.category_id
    
    # Only update fields that are provided
    if expense_update.title is not None:
        expense.title = expense_update.title
    if expense_update.amount is not None:
        expense.amount = expense_update.amount
    if expense_update.description is not None:
        expense.description = expense_update.description
    if expense_update.date is not None:
        expense.date = expense_update.date
    
    db.commit()
    db.refresh(expense)
    
    # Invalidate insights cache so dashboard shows fresh data
    insight_cache.invalidate(current_user.id)
    
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an expense"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    db.delete(expense)
    db.commit()
    
    # Invalidate insights cache so dashboard shows fresh data
    insight_cache.invalidate(current_user.id)
    
    return None
