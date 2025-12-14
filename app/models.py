from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class GoalStatus(enum.Enum):
    """Enum for goal status"""
    active = "active"
    completed = "completed"
    paused = "paused"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    # Relationships - one user has many categories, incomes, expenses, goals
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    """Category model - each user can have their own categories (e.g., Food, Rent, Entertainment)"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # index=True for fast queries
    
    # Relationships
    user = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")


class Income(Base):
    """Income model - track income sources for each user"""
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)  # Numeric for precise money, not float!
    source = Column(String(200), nullable=True)  # Optional: "Salary", "Freelance", etc.
    date = Column(DateTime, default=datetime.utcnow, nullable=False)  # Default to current time
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="incomes")


class Expense(Base):
    """Expense model - track expenses with category for each user"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Numeric for precise money
    description = Column(Text, nullable=True)  # Optional description
    date = Column(DateTime, default=datetime.utcnow, nullable=False)  # Default to current time
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")   


class Goal(Base):
    """Goal model - track financial goals with timeline calculation"""
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)  # "Buy Laptop", "Emergency Fund"
    target_amount = Column(Numeric(10, 2), nullable=False)  # Target amount to achieve
    savings_rate = Column(Numeric(3, 2), default=0.20, nullable=False)  # Default 20% of income
    status = Column(Enum(GoalStatus), default=GoalStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Start date = created date
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")   
