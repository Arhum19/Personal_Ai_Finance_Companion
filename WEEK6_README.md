# Finance Companion - Week 6: AI Insights & Forecasting

## Overview

Week 6 adds intelligent financial analysis to Finance Companion. The system now:

1. **Analyzes spending patterns** - Breakdown by category, weekday vs weekend
2. **Tracks financial trends** - Month-over-month comparison, savings rate
3. **Forecasts goals** - When you'll complete each goal at current pace
4. **Explains with AI** - GPT-powered insights that are always explainable
5. **Simulates scenarios** - "What if I spend 20% less on food?" analysis
6. **Caches intelligently** - 24-hour cache prevents excessive API costs

## New Endpoints

### GET /insights/spending

Get comprehensive spending analysis with AI insights.

**Request:**

```bash
curl -X GET "http://localhost:8000/insights/spending" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "spending_summary": {
    "period_days": 30,
    "total_spent": 45000,
    "average_daily_spend": 1500,
    "category_breakdown": {
      "Food": 15000,
      "Transport": 10000,
      "Entertainment": 8000,
      "Other": 12000
    },
    "top_category": "Food",
    "weekday_vs_weekend": {
      "weekday_average": 1400,
      "weekend_average": 1600
    },
    "expense_count": 30,
    "highest_day_spend": 5000,
    "lowest_day_spend": 200
  },
  "income_expense": {
    "total_income": 110000,
    "total_expense": 45000,
    "gross_savings": 65000,
    "savings_rate_percent": 59.1,
    "income_sources": {
      "Salary": 100000,
      "Freelance": 10000
    }
  },
  "goals": {
    "active_goals": [
      {
        "id": 1,
        "title": "Laptop",
        "target": 100000,
        "contributed": 30000,
        "remaining": 70000,
        "months_to_complete": 6.4,
        "estimated_completion": "2026-07-10",
        "on_track": true
      }
    ],
    "total_active": 1,
    "feasibility": "achievable"
  },
  "month_comparison": {
    "current_month": {
      "total_spent": 45000,
      "num_transactions": 30
    },
    "previous_month": {
      "total_spent": 42000,
      "num_transactions": 28
    },
    "percent_change": 7.1,
    "trend": "increasing"
  },
  "ai_insights": {
    "insights": [
      "Your spending increased 7% this month, primarily in Food category"
    ],
    "suggestions": [
      "Consider meal planning to reduce food expenses by 10-15%",
      "Weekend spending is 14% higher than weekdays - review leisure activities"
    ]
  },
  "source": "api"
}
```

### POST /insights/what-if

Simulate impact of spending change.

**Request:**

```bash
curl -X POST "http://localhost:8000/insights/what-if" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"category": "Food", "percent_change": -20}'
```

**Response:**

```json
{
  "simulation": {
    "category": "Food",
    "percent_change": -20,
    "current_category_amount": 15000,
    "new_category_amount": 12000,
    "category_change_amount": -3000,
    "current_total_expense": 45000,
    "new_total_expense": 42000,
    "monthly_income": 110000,
    "current_savings": 65000,
    "new_savings": 68000,
    "savings_impact": 3000,
    "current_savings_rate": 59.1,
    "new_savings_rate": 61.8,
    "sustainable": true,
    "adequate_for_goals": true
  },
  "ai_explanation": {
    "sustainable": true,
    "impact": "Reducing food spending by 20% would save you ₹3,000 monthly, increasing your savings rate from 59.1% to 61.8%.",
    "risk_level": "low",
    "recommendation": "This change is highly sustainable and would accelerate goal completion by approximately 2-3 months."
  }
}
```

## Setup Instructions

### 1. Get OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up or login
3. Go to Account > API Keys
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-...`)

### 2. Create .env File

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

**IMPORTANT:** Never commit `.env` to git (it's already in `.gitignore`)

### 3. Install New Dependencies

```bash
pip install -r requirements.txt
```

New packages added:

- `httpx==0.24.1` - Async HTTP client for OpenRouter API
- `python-dotenv==1.2.1` - Already included, loads .env file

### 4. Restart Server

```bash
uvicorn app.main:app --reload --port 8000
```

## Architecture

### Data Flow

```
User Request
    ↓
Cache Check (24-hour TTL)
    ↓
If Not Cached:
    ↓
    ├─→ insight_service.py (Pure SQL & Math)
    │   ├─ get_spending_summary() - GROUP BY category
    │   ├─ get_income_expense_snapshot() - Savings rate
    │   ├─ get_goal_forecast() - Completion dates
    │   └─ compare_month_over_month() - Trends
    │
    ├─→ ai_insights.py (Safe AI Prompts)
    │   ├─ call_openrouter() - API wrapper
    │   ├─ generate_spending_insights() - Explain patterns
    │   └─ explain_what_if_impact() - Explain scenarios
    │
    └─→ Cache Result (24 hours)

Response to User
```

### File Structure

```
app/
├── services/
│   ├── insight_service.py    (All calculations - NO AI)
│   └── ai_insights.py         (AI explanations - NO math)
├── routes/
│   └── insights.py            (API endpoints)
├── cache.py                   (24-hour cache)
└── main.py                    (Updated with insights router)
```

## Key Design Decisions

### 1. NO AI Math

- All financial calculations happen in `insight_service.py` using pure SQL/Python
- AI only explains, never calculates
- Ensures explainability and prevents hallucinations

### 2. 24-Hour Cache

- First call hits OpenRouter API
- Subsequent calls within 24 hours return cached result
- Cache invalidates on new expense/income
- **Cost benefit:** Typical user = 1-2 API calls/day instead of unlimited

### 3. Safe Prompts

- Prompts send only aggregated numbers, never raw data
- Requests JSON responses (validated)
- Fallback responses if AI fails or returns invalid JSON
- **Never exposes OpenRouter errors to user**

### 4. Input Validation

- Category: 1-50 characters
- Percent change: -100 to +500
- All inputs validated before processing

## Testing Checklist

### Manual Testing via Swagger

1. Go to http://localhost:8000/docs
2. Login (if needed)
3. Try GET /insights/spending

   - Check: All numbers are realistic
   - Check: AI suggestions match spending data
   - Check: "source" field shows "api" on first call, "cached" on second

4. Try POST /insights/what-if
   - Category: "Food", percent_change: 20
   - Check: new_savings = current_savings - (20% of Food)
   - Check: AI explanation is clear
   - Check: risk_level is low/medium/high

### Edge Cases

```bash
# Insufficient data (user with 0 expenses)
GET /insights/spending
# Expected: "insufficient_data": true

# Invalid category
POST /insights/what-if {"category": "XYZ", "percent_change": 10}
# Expected: 400 error - "No spending in 'XYZ' found"

# Invalid percent change
POST /insights/what-if {"category": "Food", "percent_change": 600}
# Expected: 400 error - validation error

# No income recorded
POST /insights/what-if {"category": "Food", "percent_change": 50}
# Expected: 400 error - "No income recorded this period"

# Without OpenRouter key
GET /insights/spending
# Expected: Works but uses fallback AI responses
```

## Cost Analysis

### OpenRouter Pricing (gpt-3.5-turbo)

- Input: ~$0.50 per 1M tokens
- Output: ~$1.50 per 1M tokens
- Typical call: ~600 tokens input, ~300 tokens output

**Per call cost:** ~$0.0006 (less than 1 cent)

**Monthly cost (example):**

- Typical user: 1-2 API calls/day
- 30 days × 2 calls × $0.0006 = **$0.036 (3.6 cents)**

**Cost saved by caching:**

- Without cache: 30 calls/day × $0.0006 = $0.18
- With 24-hour cache: 1 API call/day × $0.0006 = $0.006
- **Savings: 97%**

## Future Improvements (v2)

- Multi-scenario comparison ("compare Food -20% vs Transport -10%")
- Seasonal analysis (if 12+ months data exists)
- Anomaly detection (flag unusual spending spikes)
- Budget limits per category with alerts
- PDF reports with charts

## Troubleshooting

### Issue: "OPENROUTER_API_KEY not set"

**Solution:** Check .env file exists and has correct key format (sk-or-v1-...)

### Issue: Cache not working

**Solution:** Check first call returns "source": "api", second call returns "source": "cached"

### Issue: AI returns "Unable to analyze"

**Solution:** Ensure user has expenses in last 30 days

### Issue: API timeout (>10 seconds)

**Solution:** OpenRouter might be slow, try again. Timeout is set to 10 seconds.

## Documentation

- All functions have detailed docstrings
- All prompts are hardcoded (no prompt injection risk)
- All responses validated before returning to user
- API documented in Swagger at /docs
