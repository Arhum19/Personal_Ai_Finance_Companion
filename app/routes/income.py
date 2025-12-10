from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from decimal import Decimal

from app.dependencies import get_db, get_current_user
from app.models import User, Income
from app.schemas import IncomeCreate, IncomeUpdate, IncomeResponse, IncomeTotalResponse

router = APIRouter(prefix="/income", tags=["Income"])


@router.post("/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    income: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new income record"""
    db_income = Income(
        amount=income.amount,
        source=income.source,
        date=income.date or datetime.utcnow(),  # Default to now if not provided
        user_id=current_user.id
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income


@router.get("/", response_model=List[IncomeResponse])
def get_incomes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all incomes for the logged-in user"""
    incomes = db.query(Income).filter(
        Income.user_id == current_user.id
    ).order_by(Income.date.desc()).offset(skip).limit(limit).all()
    return incomes


@router.get("/total", response_model=IncomeTotalResponse)
def get_total_income(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total income for the logged-in user"""
    result = db.query(
        func.coalesce(func.sum(Income.amount), 0).label("total"),
        func.count(Income.id).label("count")
    ).filter(Income.user_id == current_user.id).first()
    
    return {
        "total_income": Decimal(result.total) if result.total else Decimal("0"),
        "count": result.count
    }


@router.get("/{income_id}", response_model=IncomeResponse)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific income by ID"""
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id
    ).first()
    
    if not income:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income not found"
        )
    return income


@router.put("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    income_update: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an income record"""
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id
    ).first()
    
    if not income:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income not found"
        )
    
    # Only update fields that are provided
    if income_update.amount is not None:
        income.amount = income_update.amount
    if income_update.source is not None:
        income.source = income_update.source
    if income_update.date is not None:
        income.date = income_update.date
    
    db.commit()
    db.refresh(income)
    return income


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an income record"""
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == current_user.id
    ).first()
    
    if not income:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income not found"
        )
    
    db.delete(income)
    db.commit()
    return None
