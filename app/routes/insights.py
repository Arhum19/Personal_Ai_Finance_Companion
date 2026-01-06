"""
API Routes for Financial Insights and Analysis

GET /insights/spending - Comprehensive spending analysis with AI insights
POST /insights/what-if - Simulate spending changes and show impact
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import User
from app.services.insight_service import (
    get_spending_summary,
    get_income_expense_snapshot,
    get_goal_forecast,
    compare_month_over_month,
    simulate_expense_change
)
from app.services.ai_insights import (
    generate_spending_insights,
    explain_what_if_impact
)
from app.cache import insight_cache

router = APIRouter(prefix="/insights", tags=["Insights"])


# Request/Response Models
class WhatIfRequest(BaseModel):
    """Request body for what-if simulation"""
    category: str = Field(..., min_length=1, max_length=50, description="Expense category name")
    percent_change: float = Field(..., ge=-100, le=500, description="Percent change: -100 to +500")


class SpendingSummaryResponse(BaseModel):
    """Spending summary response"""
    period_days: int
    total_spent: float
    average_daily_spend: float
    category_breakdown: dict
    top_category: str
    weekday_vs_weekend: dict
    expense_count: int
    highest_day_spend: float
    lowest_day_spend: float


class InsightResponse(BaseModel):
    """AI insight response"""
    insights: list[str]
    suggestions: list[str]
    model: str = "gpt-3.5-turbo"


class SpendingInsightsResponse(BaseModel):
    """Complete spending insights response"""
    spending_summary: dict
    income_expense: dict
    goals: dict
    month_comparison: dict
    ai_insights: InsightResponse
    source: str = "api"  # "api" or "cached"


class WhatIfSimulationResponse(BaseModel):
    """What-if simulation response"""
    simulation: dict
    ai_explanation: dict


@router.get("/spending", response_model=SpendingInsightsResponse)
async def get_spending_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive spending analysis with AI insights.
    
    Returns:
    - Spending breakdown by category
    - Income vs expense comparison
    - Goal forecasts
    - Month-over-month trends
    - AI-generated insights and suggestions
    
    Cached for 24 hours to reduce API costs.
    """
    
    cache_key = f"insights_{current_user.id}_spending"
    
    # Check cache first
    cached = insight_cache.get(cache_key)
    if cached:
        return {"source": "cached", **cached}
    
    try:
        # Get all data
        spending_summary = get_spending_summary(db, current_user.id)
        income_snapshot = get_income_expense_snapshot(db, current_user.id)
        goal_forecast = get_goal_forecast(db, current_user.id)
        month_comparison = compare_month_over_month(db, current_user.id)
        
        # Generate AI insights
        ai_insights = await generate_spending_insights(spending_summary)
        
        result = {
            "spending_summary": spending_summary,
            "income_expense": income_snapshot,
            "goals": goal_forecast,
            "month_comparison": month_comparison,
            "ai_insights": ai_insights,
            "source": "api"
        }
        
        # Cache result
        insight_cache.set(cache_key, result)
        
        return result
    
    except Exception as e:
        import traceback
        print(f"Error in get_spending_insights: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.post("/what-if", response_model=WhatIfSimulationResponse)
async def simulate_what_if(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulate impact of spending change on savings.
    
    Example:
    {
        "category": "Food",
        "percent_change": 20
    }
    
    Returns:
    - Calculated financial impact (pure math)
    - AI explanation of sustainability
    - Risk assessment
    - Practical recommendations
    """
    
    category = request.category
    percent_change = request.percent_change
    
    try:
        # Calculate impact (pure math)
        impact = simulate_expense_change(db, current_user.id, category, percent_change)
        
        if "error" in impact:
            raise HTTPException(status_code=400, detail=impact["error"])
        
        # Get AI explanation
        ai_explanation = await explain_what_if_impact(
            {
                "monthly_income": impact["monthly_income"],
                "monthly_expense": impact["current_total_expense"],
                "monthly_savings": impact["current_savings"]
            },
            {
                "category": category,
                "percent_change": percent_change,
                "new_category_amount": impact["new_category_amount"],
                "new_total_expense": impact["new_total_expense"],
                "new_savings": impact["new_savings"],
                "new_savings_rate": impact["new_savings_rate"]
            }
        )
        
        return {
            "simulation": impact,
            "ai_explanation": ai_explanation
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to run simulation")


@router.post("/cache/invalidate")
async def invalidate_cache(
    current_user: User = Depends(get_current_user)
):
    """
    Manually invalidate user's insight cache.
    
    Called automatically after new expense/income.
    Can also be called manually if needed.
    """
    insight_cache.invalidate(current_user.id)
    return {"message": f"Cache invalidated for user {current_user.id}"}
