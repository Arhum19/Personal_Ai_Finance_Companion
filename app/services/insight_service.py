"""
Insight Service for Financial Analysis

All calculations are deterministic and based on real data from database.
No AI involved - pure SQL and Python math.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from app.models import Expense, Income, Goal, GoalContribution, Category


def get_spending_summary(db: Session, user_id: int, days: int = 30) -> dict:
    """
    Get comprehensive spending analysis for last N days.
    
    Returns:
        {
            "period_days": 30,
            "total_spent": 45000,
            "average_daily_spend": 1500,
            "category_breakdown": {"Food": 15000, ...},
            "top_category": "Food",
            "weekday_vs_weekend": {...},
            "expense_count": 30,
            "highest_day_spend": 5000,
            "lowest_day_spend": 200
        }
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query expenses for period
    expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == user_id,
            Expense.date >= start_date
        )
    ).all()
    
    if not expenses:
        return {
            "period_days": days,
            "total_spent": 0,
            "average_daily_spend": 0,
            "category_breakdown": {},
            "top_category": "N/A",
            "weekday_vs_weekend": {
                "weekday_average": 0,
                "weekend_average": 0
            },
            "expense_count": 0,
            "highest_day_spend": 0,
            "lowest_day_spend": 0,
            "insufficient_data": True
        }
    
    # Category breakdown
    category_breakdown = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else "Other"
        category_breakdown[cat_name] = category_breakdown.get(cat_name, 0) + float(exp.amount)
    
    # Total spent
    total_spent = sum(float(e.amount) for e in expenses)
    
    # Average daily spend
    unique_days = len(set(e.date.date() for e in expenses))
    average_daily_spend = total_spent / unique_days if unique_days > 0 else 0
    
    # Weekday vs weekend
    weekday_amounts = []
    weekend_amounts = []
    
    for exp in expenses:
        day_of_week = exp.date.weekday()  # 0=Mon, 6=Sun
        amount = float(exp.amount)
        
        if day_of_week < 5:  # Mon-Fri
            weekday_amounts.append(amount)
        else:  # Sat-Sun
            weekend_amounts.append(amount)
    
    weekday_avg = sum(weekday_amounts) / len(weekday_amounts) if weekday_amounts else 0
    weekend_avg = sum(weekend_amounts) / len(weekend_amounts) if weekend_amounts else 0
    
    # Daily spending stats
    daily_totals = {}
    for exp in expenses:
        date_key = exp.date.date()
        daily_totals[date_key] = daily_totals.get(date_key, 0) + float(exp.amount)
    
    highest_day_spend = max(daily_totals.values()) if daily_totals else 0
    lowest_day_spend = min(daily_totals.values()) if daily_totals else 0
    
    # Top category
    top_category = max(category_breakdown, key=category_breakdown.get) if category_breakdown else "N/A"
    
    return {
        "period_days": days,
        "total_spent": round(total_spent, 2),
        "average_daily_spend": round(average_daily_spend, 2),
        "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
        "top_category": top_category,
        "weekday_vs_weekend": {
            "weekday_average": round(weekday_avg, 2),
            "weekend_average": round(weekend_avg, 2)
        },
        "expense_count": len(expenses),
        "highest_day_spend": round(highest_day_spend, 2),
        "lowest_day_spend": round(lowest_day_spend, 2)
    }


def get_income_expense_snapshot(db: Session, user_id: int, days: int = 30) -> dict:
    """
    Get income vs expense summary for last N days.
    
    Returns:
        {
            "period_days": 30,
            "total_income": 110000,
            "total_expense": 45000,
            "gross_savings": 65000,
            "savings_rate_percent": 59.1,
            "average_daily_income": 3667,
            "average_daily_expense": 1500,
            "income_sources": {"Salary": 100000, ...}
        }
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query income
    incomes = db.query(Income).filter(
        and_(
            Income.user_id == user_id,
            Income.date >= start_date
        )
    ).all()
    
    # Query expenses
    expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == user_id,
            Expense.date >= start_date
        )
    ).all()
    
    # Calculate totals
    total_income = sum(float(i.amount) for i in incomes)
    total_expense = sum(float(e.amount) for e in expenses)
    gross_savings = total_income - total_expense
    
    # Savings rate
    savings_rate_percent = (gross_savings / total_income * 100) if total_income > 0 else 0
    
    # Daily averages
    unique_income_days = len(set(i.date.date() for i in incomes)) if incomes else 1
    unique_expense_days = len(set(e.date.date() for e in expenses)) if expenses else 1
    
    average_daily_income = total_income / unique_income_days if unique_income_days > 0 else 0
    average_daily_expense = total_expense / unique_expense_days if unique_expense_days > 0 else 0
    
    # Income sources breakdown
    income_sources = {}
    for inc in incomes:
        source = inc.source if inc.source else "Other"
        income_sources[source] = income_sources.get(source, 0) + float(inc.amount)
    
    return {
        "period_days": days,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "gross_savings": round(gross_savings, 2),
        "savings_rate_percent": round(savings_rate_percent, 1),
        "average_daily_income": round(average_daily_income, 2),
        "average_daily_expense": round(average_daily_expense, 2),
        "income_sources": {k: round(v, 2) for k, v in income_sources.items()}
    }


def get_goal_forecast(db: Session, user_id: int) -> dict:
    """
    Get forecast for all active goals with completion estimates.
    
    Returns:
        {
            "active_goals": [
                {
                    "id": 1,
                    "title": "Laptop",
                    "target": 100000,
                    "contributed": 30000,
                    "monthly_contribution": 11000,
                    "remaining": 70000,
                    "months_to_complete": 6.4,
                    "estimated_completion": "2026-07-10",
                    "on_track": true
                }
            ],
            "total_active": 2,
            "total_monthly_allocation": 22000,
            "required_monthly_income": 110000,
            "feasibility": "achievable"
        }
    """
    # Get active goals
    goals = db.query(Goal).filter(
        and_(
            Goal.user_id == user_id,
            Goal.status == "active"
        )
    ).all()
    
    if not goals:
        return {
            "active_goals": [],
            "total_active": 0,
            "total_monthly_allocation": 0,
            "required_monthly_income": 0,
            "feasibility": "N/A"
        }
    
    # Get monthly income for context
    start_date = datetime.utcnow() - timedelta(days=30)
    monthly_income = db.query(func.sum(Income.amount)).filter(
        and_(
            Income.user_id == user_id,
            Income.date >= start_date
        )
    ).scalar() or 0
    monthly_income = float(monthly_income)
    
    # Calculate total savings pool (20% of income by default)
    total_savings_pool = monthly_income * 0.20 if monthly_income > 0 else 0
    suggested_per_goal = total_savings_pool / len(goals) if len(goals) > 0 else 0
    
    # Process each goal
    active_goals_list = []
    total_monthly_allocation = 0
    
    for goal in goals:
        # Get contributions for this goal
        contributions = db.query(func.sum(GoalContribution.amount)).filter(
            GoalContribution.goal_id == goal.id
        ).scalar() or 0
        contributed = float(contributions)
        
        target = float(goal.target_amount)
        remaining = target - contributed
        
        # Use calculated suggested monthly contribution
        savings_rate = float(goal.savings_rate) if goal.savings_rate else 0.20
        goal_savings_pool = monthly_income * savings_rate
        monthly_contribution = goal_savings_pool / len(goals) if len(goals) > 0 else 0
        
        if monthly_contribution > 0 and remaining > 0:
            months_to_complete = remaining / monthly_contribution
            completion_date = datetime.utcnow() + timedelta(days=months_to_complete * 30)
            estimated_completion = completion_date.strftime("%Y-%m-%d")
        elif remaining <= 0:
            months_to_complete = 0
            estimated_completion = "Completed"
        else:
            months_to_complete = float('inf')
            estimated_completion = "Unknown (no income)"
        
        # Check if on track
        on_track = True if months_to_complete != float('inf') and months_to_complete < 100 else False
        
        active_goals_list.append({
            "id": goal.id,
            "title": goal.title,
            "target": round(target, 2),
            "contributed": round(contributed, 2),
            "monthly_contribution": round(monthly_contribution, 2),
            "remaining": round(remaining, 2),
            "months_to_complete": round(months_to_complete, 1) if months_to_complete != float('inf') else None,
            "estimated_completion": estimated_completion,
            "on_track": on_track
        })
        
        total_monthly_allocation += monthly_contribution
    
    # Feasibility check
    if monthly_income > 0:
        allocation_percentage = (total_monthly_allocation / monthly_income) * 100
        if allocation_percentage <= 20:
            feasibility = "achievable"
        elif allocation_percentage <= 40:
            feasibility = "challenging"
        else:
            feasibility = "risky"
    else:
        feasibility = "unknown (no income)"
    
    return {
        "active_goals": active_goals_list,
        "total_active": len(active_goals_list),
        "total_monthly_allocation": round(total_monthly_allocation, 2),
        "required_monthly_income": round(monthly_income, 2),
        "feasibility": feasibility
    }


def compare_month_over_month(db: Session, user_id: int) -> dict:
    """
    Compare current month spending to previous month.
    
    Returns:
        {
            "current_month": {"total_spent": 45000, "num_transactions": 30},
            "previous_month": {"total_spent": 42000, "num_transactions": 28},
            "percent_change": 7.1,
            "trend": "increasing",
            "velocity": "moderate"
        }
    """
    today = datetime.utcnow()
    current_month_start = today.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    
    # Current month expenses
    current_expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == user_id,
            Expense.date >= current_month_start,
            Expense.date <= today
        )
    ).all()
    
    # Previous month expenses
    previous_expenses = db.query(Expense).filter(
        and_(
            Expense.user_id == user_id,
            Expense.date >= previous_month_start,
            Expense.date <= previous_month_end
        )
    ).all()
    
    current_total = sum(float(e.amount) for e in current_expenses)
    previous_total = sum(float(e.amount) for e in previous_expenses)
    
    # Calculate change
    if previous_total > 0:
        percent_change = ((current_total - previous_total) / previous_total) * 100
    else:
        percent_change = 0 if current_total == 0 else 100
    
    # Determine trend
    if abs(percent_change) <= 5:
        trend = "stable"
    elif percent_change > 5:
        trend = "increasing"
    else:
        trend = "decreasing"
    
    # Velocity
    if abs(percent_change) <= 2:
        velocity = "minimal"
    elif abs(percent_change) <= 10:
        velocity = "moderate"
    else:
        velocity = "significant"
    
    return {
        "current_month": {
            "total_spent": round(current_total, 2),
            "num_transactions": len(current_expenses)
        },
        "previous_month": {
            "total_spent": round(previous_total, 2),
            "num_transactions": len(previous_expenses)
        },
        "percent_change": round(percent_change, 1),
        "trend": trend,
        "velocity": velocity
    }


def simulate_expense_change(
    db: Session,
    user_id: int,
    category_name: str,
    percent_change: float,
    days: int = 30
) -> dict:
    """
    Calculate impact of spending change on savings and goals.
    
    Args:
        category_name: Name of category to modify (e.g., "Food")
        percent_change: +20 = 20% increase, -50 = 50% decrease
        days: Period to analyze (default 30)
    
    Returns:
        Calculated impact (pure math, no AI)
    """
    
    # Validate input
    if percent_change < -100 or percent_change > 500:
        return {"error": "Percent change must be between -100 and +500"}
    
    if not category_name or len(category_name) > 50:
        return {"error": "Invalid category name"}
    
    # Get current spending
    current_summary = get_spending_summary(db, user_id, days)
    income_snapshot = get_income_expense_snapshot(db, user_id, days)
    
    if not current_summary.get("total_spent") or current_summary.get("insufficient_data"):
        return {"error": "Insufficient spending data"}
    
    # Get category current amount
    category_current = current_summary.get("category_breakdown", {}).get(category_name, 0)
    
    if category_current == 0:
        return {"error": f"No spending in '{category_name}' found"}
    
    # Calculate new amounts
    category_change_amount = category_current * (percent_change / 100)
    new_category_amount = category_current + category_change_amount
    
    # Ensure not negative
    if new_category_amount < 0:
        new_category_amount = 0
    
    # Recalculate totals
    spending_difference = new_category_amount - category_current
    new_total_expense = current_summary["total_spent"] + spending_difference
    monthly_income = income_snapshot["total_income"]
    
    if monthly_income <= 0:
        return {"error": "No income recorded this period"}
    
    new_savings = monthly_income - new_total_expense
    new_savings_rate = (new_savings / monthly_income * 100) if monthly_income > 0 else 0
    
    return {
        "category": category_name,
        "percent_change": percent_change,
        "current_category_amount": round(category_current, 2),
        "new_category_amount": round(new_category_amount, 2),
        "category_change_amount": round(category_change_amount, 2),
        "current_total_expense": round(current_summary["total_spent"], 2),
        "new_total_expense": round(new_total_expense, 2),
        "monthly_income": round(monthly_income, 2),
        "current_savings": round(income_snapshot["gross_savings"], 2),
        "new_savings": round(new_savings, 2),
        "savings_impact": round(new_savings - income_snapshot["gross_savings"], 2),
        "current_savings_rate": round(income_snapshot["savings_rate_percent"], 1),
        "new_savings_rate": round(new_savings_rate, 1),
        "sustainable": new_savings > 0,
        "adequate_for_goals": new_savings >= (monthly_income * 0.20)  # 20% rule
    }
