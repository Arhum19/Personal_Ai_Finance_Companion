from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    
    # Relationships - one user has many categories, incomes, expenses
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")


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
