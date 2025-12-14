from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user
from app.models import User, Goal, GoalStatus
from app.schemas import (
    GoalCreate, 
    GoalUpdate, 
    GoalResponse, 
    GoalProgressResponse,
    AllGoalsProgressResponse
)
from app.services.goal_service import (
    get_goal_with_progress,
    get_all_goals_with_progress
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
