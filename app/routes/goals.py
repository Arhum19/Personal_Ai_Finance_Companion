from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from decimal import Decimal

from app.dependencies import get_db, get_current_user
from app.models import User, Goal, GoalStatus, GoalContribution, Income, Expense
from app.schemas import (
    GoalCreate, 
    GoalUpdate, 
    GoalResponse, 
    GoalProgressResponse,
    AllGoalsProgressResponse,
    GoalContributionCreate,
    GoalContributionResponse,
    GoalContributionsListResponse
)
from app.services.goal_service import (
    get_goal_with_progress,
    get_all_goals_with_progress,
    get_goal_contributions,
    check_and_complete_goal
)

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("/", response_model=GoalProgressResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new financial goal.
    
    Example: "I want to buy laptop for 50000"
    - title: "Buy Laptop"
    - target_amount: 50000
    - savings_rate: 0.20 (default 20%, user can customize)
    
    Returns the goal with calculated timeline based on current income.
    """
    db_goal = Goal(
        title=goal.title,
        target_amount=goal.target_amount,
        savings_rate=goal.savings_rate,
        user_id=current_user.id
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    # Return with calculated progress
    return get_goal_with_progress(db, db_goal, current_user.id)


@router.get("/", response_model=AllGoalsProgressResponse)
def get_goals(
    include_inactive: bool = Query(False, description="Include completed/paused goals"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all goals with progress calculations.
    
    Returns:
    - Monthly income (current month)
    - Total savings pool (20% of income shared among goals)
    - Each goal with timeline and progress percentage
    
    Perfect for dashboard visualization!
    """
    return get_all_goals_with_progress(db, current_user.id, include_inactive)


@router.get("/{goal_id}", response_model=GoalProgressResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single goal with detailed progress calculation."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return get_goal_with_progress(db, goal, current_user.id)


@router.put("/{goal_id}", response_model=GoalProgressResponse)
def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a goal.
    
    Can update:
    - title
    - target_amount
    - savings_rate
    - status (active, completed, paused)
    """
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Update fields if provided
    if goal_update.title is not None:
        goal.title = goal_update.title
    if goal_update.target_amount is not None:
        goal.target_amount = goal_update.target_amount
    if goal_update.savings_rate is not None:
        goal.savings_rate = goal_update.savings_rate
    if goal_update.status is not None:
        try:
            goal.status = GoalStatus(goal_update.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: active, completed, paused"
            )
    
    db.commit()
    db.refresh(goal)
    
    return get_goal_with_progress(db, goal, current_user.id)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    db.delete(goal)
    db.commit()
    return None


@router.post("/{goal_id}/complete", response_model=GoalResponse)
def mark_goal_complete(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a goal as completed."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    goal.status = GoalStatus.completed
    db.commit()
    db.refresh(goal)
    
    return {
        "id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "savings_rate": goal.savings_rate,
        "status": goal.status.value,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "user_id": goal.user_id
    }


@router.post("/{goal_id}/pause", response_model=GoalResponse)
def pause_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause a goal (won't count towards active goals)."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    goal.status = GoalStatus.paused
    db.commit()
    db.refresh(goal)
    
    return {
        "id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "savings_rate": goal.savings_rate,
        "status": goal.status.value,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "user_id": goal.user_id
    }


@router.post("/{goal_id}/resume", response_model=GoalProgressResponse)
def resume_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume a paused goal."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    goal.status = GoalStatus.active
    db.commit()
    db.refresh(goal)
    
    return get_goal_with_progress(db, goal, current_user.id)


# ==================== CONTRIBUTION ENDPOINTS ====================

@router.post("/{goal_id}/contribute", response_model=GoalProgressResponse, status_code=status.HTTP_201_CREATED)
def contribute_to_goal(
    goal_id: int,
    contribution: GoalContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a contribution to a goal.
    
    This is where REAL money is allocated to the goal.
    The contribution will be deducted from 'available_to_spend' in balance.
    
    Example: "Contribute 20000 to laptop goal"
    """
    # Find the goal
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    if goal.status != GoalStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot contribute to a {goal.status.value} goal. Resume it first."
        )
    
    # ===== VALIDATION: Check if user has sufficient available balance =====
    # Calculate current financial balance
    income_result = db.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(Income.user_id == current_user.id).scalar()
    
    expense_result = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.user_id == current_user.id).scalar()
    
    current_goal_contributions = db.query(
        func.coalesce(func.sum(GoalContribution.amount), 0)
    ).filter(GoalContribution.user_id == current_user.id).scalar()
    
    total_income = Decimal(income_result) if income_result else Decimal("0")
    total_expense = Decimal(expense_result) if expense_result else Decimal("0")
    current_contributions = Decimal(current_goal_contributions) if current_goal_contributions else Decimal("0")
    
    remaining_balance = total_income - total_expense
    available_to_spend = remaining_balance - current_contributions
    contribution_amount = Decimal(str(contribution.amount))
    
    # FIRST CHECK: If available balance is already zero or negative, reject any contribution
    if available_to_spend <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot contribute to goal. Your available balance is insufficient. "
                   f"Total income: ${float(total_income):.2f}. "
                   f"Total expenses: ${float(total_expense):.2f}. "
                   f"Current goal contributions: ${float(current_contributions):.2f}. "
                   f"Available balance: ${float(available_to_spend):.2f}. "
                   f"Please increase your income or reduce expenses/other goal contributions."
        )
    
    # SECOND CHECK: If contribution exceeds available balance, reject it
    if contribution_amount > available_to_spend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds for this contribution. "
                   f"Available balance: ${float(available_to_spend):.2f}. "
                   f"Requested contribution: ${float(contribution_amount):.2f}. "
                   f"Please contribute an amount equal to or less than ${float(available_to_spend):.2f}."
        )
    
    # Create the contribution
    db_contribution = GoalContribution(
        amount=contribution.amount,
        date=contribution.date or datetime.utcnow(),
        goal_id=goal.id,
        user_id=current_user.id
    )
    db.add(db_contribution)
    db.commit()
    
    # Check if goal is now complete
    goal_completed = check_and_complete_goal(db, goal)
    
    # Refresh goal to get updated status
    db.refresh(goal)
    
    # Return goal with updated progress
    result = get_goal_with_progress(db, goal, current_user.id)
    
    # Add completion message if applicable
    if goal_completed:
        result["message"] = "🎉 Goal completed!"
    
    return result


@router.get("/{goal_id}/contributions", response_model=GoalContributionsListResponse)
def get_goal_contributions_list(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all contributions for a specific goal.
    
    Useful for seeing contribution history.
    """
    # Find the goal
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Get contributions
    contributions = db.query(GoalContribution).filter(
        GoalContribution.goal_id == goal_id,
        GoalContribution.user_id == current_user.id
    ).order_by(GoalContribution.date.desc()).all()
    
    # Calculate total
    total_contributed = get_goal_contributions(db, goal_id)
    
    return {
        "goal_id": goal.id,
        "goal_title": goal.title,
        "target_amount": goal.target_amount,
        "total_contributed": total_contributed,
        "contributions": [
            {
                "id": c.id,
                "amount": c.amount,
                "date": c.date,
                "goal_id": c.goal_id,
                "user_id": c.user_id,
                "goal_title": goal.title
            }
            for c in contributions
        ]
    }


@router.delete("/contributions/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a contribution.
    
    Use this if a contribution was made by mistake.
    """
    contribution = db.query(GoalContribution).filter(
        GoalContribution.id == contribution_id,
        GoalContribution.user_id == current_user.id
    ).first()
    
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    # Get the goal to potentially revert its status
    goal = db.query(Goal).filter(Goal.id == contribution.goal_id).first()
    
    db.delete(contribution)
    db.commit()
    
    # If goal was completed, check if it should be reverted to active
    if goal and goal.status == GoalStatus.completed:
        new_total = get_goal_contributions(db, goal.id)
        if new_total < goal.target_amount:
            goal.status = GoalStatus.active
            db.commit()
    
    return None
