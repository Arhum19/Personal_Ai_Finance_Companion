import { useState, useEffect, useMemo } from "react";
import {
  FaLightbulb,
  FaMagic,
  FaChartLine,
  FaRobot,
  FaCheckCircle,
  FaChartBar,
  FaChartArea,
} from "react-icons/fa";
import toast from "react-hot-toast";
import MainLayout from "../layouts/MainLayout";
import {
  insightsAPI,
  categoryAPI,
  expenseAPI,
  incomeAPI,
} from "../services/api";
import {
  MonthlyComparisonChart,
  CumulativeSpendingChart,
  CategoryRadarChart,
  IncomeVsSavingsChart,
  WeekdaySpendingChart,
} from "../components/Charts";

const InsightsPage = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [allCategories, setAllCategories] = useState([]); // All available categories
  const [expenses, setExpenses] = useState([]);
  const [incomes, setIncomes] = useState([]);
  const [activeChartTab, setActiveChartTab] = useState("comparison");

  const [whatIfData, setWhatIfData] = useState({
    category: "",
    percent_change: "10",
  });

  useEffect(() => {
    fetchInsights();
    fetchAllCategories();
    fetchExpenses();
    fetchIncomes();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const response = await insightsAPI.getSpendingInsights();
      setInsights(response.data || {});
    } catch (error) {
      console.error("Error fetching insights:", error);
      toast.error("Failed to load insights");
    } finally {
      setLoading(false);
    }
  };

  const fetchAllCategories = async () => {
    try {
      const response = await categoryAPI.getAll();
      const categories = response.data || [];
      setAllCategories(categories);
      // Set default category if available
      if (categories.length > 0 && !whatIfData.category) {
        setWhatIfData((prev) => ({ ...prev, category: categories[0].name }));
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const fetchExpenses = async () => {
    try {
      const response = await expenseAPI.getAll();
      setExpenses(response.data || []);
    } catch (error) {
      console.error("Error fetching expenses:", error);
    }
  };

  const fetchIncomes = async () => {
    try {
      const response = await incomeAPI.getAll();
      setIncomes(response.data || []);
    } catch (error) {
      console.error("Error fetching incomes:", error);
    }
  };

  // Prepare monthly comparison data
  const monthlyComparisonData = useMemo(() => {
    const monthData = {};
    const today = new Date();

    // Initialize last 6 months
    for (let i = 5; i >= 0; i--) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
      const key = date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });
      monthData[key] = { month: key, income: 0, expenses: 0 };
    }

    // Aggregate expenses
    expenses.forEach((exp) => {
      const date = new Date(exp.date);
      const key = date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });
      if (monthData[key]) {
        monthData[key].expenses += parseFloat(exp.amount);
      }
    });

    // Aggregate income
    incomes.forEach((inc) => {
      const date = new Date(inc.date);
      const key = date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });
      if (monthData[key]) {
        monthData[key].income += parseFloat(inc.amount);
      }
    });

    return Object.values(monthData);
  }, [expenses, incomes]);

  // Prepare cumulative spending data (last 30 days)
  const cumulativeSpendingData = useMemo(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);

    const dailyData = {};

    // Filter expenses from last 30 days
    const recentExpenses = expenses.filter(
      (exp) => new Date(exp.date) >= thirtyDaysAgo
    );

    // Sort by date
    recentExpenses.sort((a, b) => new Date(a.date) - new Date(b.date));

    let cumulative = 0;
    recentExpenses.forEach((exp) => {
      const dateKey = new Date(exp.date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
      cumulative += parseFloat(exp.amount);
      dailyData[dateKey] = { date: dateKey, cumulative };
    });

    return Object.values(dailyData);
  }, [expenses]);

  // Prepare category radar data (this month vs last month)
  const categoryRadarData = useMemo(() => {
    const today = new Date();
    const thisMonth = today.getMonth();
    const lastMonth = thisMonth === 0 ? 11 : thisMonth - 1;
    const thisYear = today.getFullYear();
    const lastYear = thisMonth === 0 ? thisYear - 1 : thisYear;

    const categoryData = {};

    expenses.forEach((exp) => {
      const date = new Date(exp.date);
      const month = date.getMonth();
      const year = date.getFullYear();
      const category = exp.category_name || "Other";

      if (!categoryData[category]) {
        categoryData[category] = { category, current: 0, previous: 0 };
      }

      if (month === thisMonth && year === thisYear) {
        categoryData[category].current += parseFloat(exp.amount);
      } else if (month === lastMonth && year === lastYear) {
        categoryData[category].previous += parseFloat(exp.amount);
      }
    });

    return Object.values(categoryData).slice(0, 8); // Limit to 8 categories for readability
  }, [expenses]);

  // Prepare income vs savings data
  const incomeVsSavingsData = useMemo(() => {
    return monthlyComparisonData.map((item) => ({
      ...item,
      savings: Math.max(0, item.income - item.expenses),
    }));
  }, [monthlyComparisonData]);

  // Prepare weekday spending data
  const weekdaySpendingData = useMemo(() => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const dayTotals = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 };
    const dayCounts = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 };

    expenses.forEach((exp) => {
      const day = new Date(exp.date).getDay();
      dayTotals[day] += parseFloat(exp.amount);
      dayCounts[day]++;
    });

    return days.map((day, index) => ({
      day,
      amount: dayCounts[index] > 0 ? dayTotals[index] / dayCounts[index] : 0,
    }));
  }, [expenses]);

  const handleWhatIfSubmit = async (e) => {
    e.preventDefault();

    try {
      const payload = {
        category: whatIfData.category,
        percent_change: parseFloat(whatIfData.percent_change),
      };

      const response = await insightsAPI.whatIf(payload);
      setWhatIfResult(response.data);
      toast.success("What-if simulation completed!");
    } catch (error) {
      console.error("Error running what-if:", error);
      toast.error(
        error.response?.data?.detail || "Failed to run what-if simulation"
      );
    }
  };

  const handleWhatIfChange = (e) => {
    setWhatIfData({
      ...whatIfData,
      [e.target.name]: e.target.value,
    });
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-8">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
            <div className="h-64 bg-gray-200 rounded-lg"></div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Handle null/undefined insights
  if (!insights) {
    return (
      <MainLayout>
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <FaLightbulb className="mx-auto text-6xl text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">No insights available yet</p>
            <p className="text-gray-400 mt-2">
              Add some expenses to get AI-powered insights
            </p>
          </div>
        </div>
      </MainLayout>
    );
  }

  const spendingSummary = insights?.spending_summary || {};
  const aiInsights = insights?.ai_insights || {};
  const incomeExpense = insights?.income_expense || {};
  const categoryBreakdown = spendingSummary?.category_breakdown || {};

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FaRobot className="text-4xl text-gradient bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text" />
            <h1 className="text-4xl font-bold text-gray-800">
              AI Financial Insights
            </h1>
          </div>
          <p className="text-gray-600 mt-2">
            Personalized spending analysis & predictions
          </p>
        </div>

        {/* Spending Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl shadow-lg p-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              Total Spent (Last 30 Days)
            </h3>
            <p className="text-3xl font-bold text-blue-600">
              ${parseFloat(spendingSummary.total_spent || 0).toFixed(2)}
            </p>
            <p className="text-sm text-blue-700 mt-2">
              Avg Daily: $
              {parseFloat(spendingSummary.average_daily_spend || 0).toFixed(2)}
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl shadow-lg p-6">
            <h3 className="text-sm font-semibold text-green-900 mb-2">
              Top Spending Category
            </h3>
            <p className="text-3xl font-bold text-green-600">
              {spendingSummary.top_category || "N/A"}
            </p>
            <p className="text-sm text-green-700 mt-2">
              {Object.entries(categoryBreakdown).length} categories tracked
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl shadow-lg p-6">
            <h3 className="text-sm font-semibold text-purple-900 mb-2">
              Expense Count
            </h3>
            <p className="text-3xl font-bold text-purple-600">
              {spendingSummary.expense_count || 0}
            </p>
            <p className="text-sm text-purple-700 mt-2">
              transactions recorded
            </p>
          </div>
        </div>

        {/* AI Insights Section */}
        {aiInsights?.insights &&
          Array.isArray(aiInsights.insights) &&
          aiInsights.insights.length > 0 && (
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl p-8 mb-8 text-white">
              <div className="flex items-start gap-4">
                <FaLightbulb className="text-5xl flex-shrink-0" />
                <div className="flex-1">
                  <h2 className="text-3xl font-bold mb-4 flex items-center gap-2">
                    <FaMagic /> AI Recommendations
                  </h2>
                  <ul className="space-y-3">
                    {aiInsights.insights.slice(0, 3).map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-lg">
                        <FaCheckCircle className="text-green-300 flex-shrink-0 mt-1" />
                        <span className="leading-relaxed">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

        {/* Suggestions Section */}
        {aiInsights?.suggestions &&
          Array.isArray(aiInsights.suggestions) &&
          aiInsights.suggestions.length > 0 && (
            <div className="bg-gradient-to-r from-orange-50 to-red-50 border-2 border-orange-200 rounded-2xl shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-orange-900 mb-4 flex items-center gap-2">
                <FaChartLine /> Action Items
              </h2>
              <ul className="space-y-3">
                {aiInsights.suggestions.map((suggestion, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 text-gray-800"
                  >
                    <span className="inline-flex items-center justify-center w-6 h-6 bg-orange-500 text-white rounded-full flex-shrink-0 text-sm font-bold">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed text-lg">
                      {suggestion}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

        {/* What-If Simulator */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <FaMagic className="text-purple-600" /> What-If Simulator
          </h2>
          <p className="text-gray-600 mb-6">
            Simulate how changes in spending categories would impact your
            finances
          </p>

          <form
            onSubmit={handleWhatIfSubmit}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Category
              </label>
              <select
                name="category"
                value={whatIfData.category}
                onChange={handleWhatIfChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              >
                {allCategories.length === 0 ? (
                  <option value="">No categories available</option>
                ) : (
                  allCategories.map((cat) => (
                    <option key={cat.id} value={cat.name}>
                      {cat.name.charAt(0).toUpperCase() + cat.name.slice(1)}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Change %
              </label>
              <div className="relative">
                <input
                  type="number"
                  name="percent_change"
                  value={whatIfData.percent_change}
                  onChange={handleWhatIfChange}
                  step="5"
                  min="-100"
                  max="500"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder="10"
                />
                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                  %
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Negative = decrease, Positive = increase
              </p>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg transition font-semibold shadow-lg"
              >
                Run Simulation
              </button>
            </div>
          </form>
        </div>

        {/* What-If Results */}
        {whatIfResult && (
          <div className="bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-200 rounded-2xl shadow-lg p-8 mb-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">
              Simulation Results
            </h3>

            {whatIfResult.simulation && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Current State */}
                <div className="bg-white rounded-xl p-6 border border-gray-200">
                  <h4 className="text-lg font-semibold text-gray-700 mb-4">
                    📊 Current State
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                      <span className="text-gray-600">Category Spending:</span>
                      <span className="font-bold text-gray-800">
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.current_category_amount || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                      <span className="text-gray-600">Total Spending:</span>
                      <span className="font-bold text-gray-800">
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.current_total_expense || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2">
                      <span className="text-gray-600 font-semibold">
                        Monthly Savings:
                      </span>
                      <span className="font-bold text-blue-600 text-lg">
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.current_savings || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {/* After Change */}
                <div className="bg-white rounded-xl p-6 border border-green-200 bg-green-50">
                  <h4 className="text-lg font-semibold text-green-700 mb-4">
                    ✨ After{" "}
                    {whatIfResult.simulation.percent_change > 0 ? "+" : ""}
                    {whatIfResult.simulation.percent_change}% Change
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center pb-2 border-b border-green-200">
                      <span className="text-gray-600">
                        New Category Spending:
                      </span>
                      <span className="font-bold text-green-700">
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.new_category_amount || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pb-2 border-b border-green-200">
                      <span className="text-gray-600">New Total Spending:</span>
                      <span className="font-bold text-green-700">
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.new_total_expense || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2">
                      <span className="text-gray-600 font-semibold">
                        New Monthly Savings:
                      </span>
                      <span
                        className={`font-bold text-lg ${
                          whatIfResult.simulation.savings_impact >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        ₹
                        {parseFloat(
                          whatIfResult.simulation.new_savings || 0
                        ).toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Savings Impact Summary */}
            {whatIfResult.simulation && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 mb-6 border border-purple-200">
                <h4 className="text-lg font-semibold text-gray-700 mb-4">
                  💰 Savings Impact
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-gray-600 text-sm">Change in Category</p>
                    <p
                      className={`text-2xl font-bold ${
                        whatIfResult.simulation.category_change_amount >= 0
                          ? "text-red-600"
                          : "text-green-600"
                      }`}
                    >
                      {whatIfResult.simulation.category_change_amount >= 0
                        ? "+"
                        : ""}
                      ₹
                      {parseFloat(
                        whatIfResult.simulation.category_change_amount || 0
                      ).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-sm">Savings Impact</p>
                    <p
                      className={`text-2xl font-bold ${
                        whatIfResult.simulation.savings_impact >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {whatIfResult.simulation.savings_impact >= 0 ? "+" : ""}₹
                      {parseFloat(
                        whatIfResult.simulation.savings_impact || 0
                      ).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-sm">New Savings Rate</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {parseFloat(
                        whatIfResult.simulation.new_savings_rate || 0
                      ).toFixed(1)}
                      %
                    </p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-purple-200">
                  <p className="text-gray-700">
                    <strong>Sustainable:</strong>{" "}
                    <span
                      className={
                        whatIfResult.simulation.sustainable
                          ? "text-green-600 font-semibold"
                          : "text-red-600 font-semibold"
                      }
                    >
                      {whatIfResult.simulation.sustainable ? "✅ Yes" : "❌ No"}
                    </span>
                  </p>
                </div>
              </div>
            )}

            {whatIfResult.ai_explanation && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h4 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <FaRobot className="text-purple-600" /> AI Explanation
                </h4>
                <p className="text-gray-700 leading-relaxed mb-4">
                  {whatIfResult.ai_explanation.impact ||
                    whatIfResult.ai_explanation.explanation}
                </p>
                {whatIfResult.ai_explanation.recommendation && (
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <p className="text-gray-700">
                      <strong>💡 Recommendation:</strong>{" "}
                      {whatIfResult.ai_explanation.recommendation}
                    </p>
                  </div>
                )}
                {whatIfResult.ai_explanation.risk_level && (
                  <p className="text-gray-600 mt-3 text-sm">
                    <strong>Risk Level:</strong>{" "}
                    <span
                      className={`font-semibold ${
                        whatIfResult.ai_explanation.risk_level === "low"
                          ? "text-green-600"
                          : whatIfResult.ai_explanation.risk_level === "medium"
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}
                    >
                      {whatIfResult.ai_explanation.risk_level.toUpperCase()}
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Category Breakdown */}
        {categoryBreakdown && Object.keys(categoryBreakdown).length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              Spending by Category
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(categoryBreakdown).map(([category, amount]) => {
                const categoryAmount = parseFloat(amount);
                const totalSpent = parseFloat(spendingSummary.total_spent || 1);
                const percentage = (categoryAmount / totalSpent) * 100;

                return (
                  <div key={category} className="bg-gray-50 rounded-xl p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-gray-700 capitalize">
                        {category}
                      </span>
                      <span className="text-sm font-bold text-gray-600">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="mt-2 text-right text-sm text-gray-600">
                      ${categoryAmount.toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Advanced Charts Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <FaChartBar className="text-blue-600" /> Advanced Analytics
            </h2>
            <div className="flex gap-2">
              {[
                { id: "comparison", label: "Comparison" },
                { id: "cumulative", label: "Cumulative" },
                { id: "radar", label: "Pattern" },
                { id: "savings", label: "Savings" },
                { id: "weekday", label: "By Day" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveChartTab(tab.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeChartTab === tab.id
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Chart Display */}
          <div className="min-h-[350px]">
            {activeChartTab === "comparison" && (
              <MonthlyComparisonChart data={monthlyComparisonData} />
            )}
            {activeChartTab === "cumulative" && (
              <CumulativeSpendingChart data={cumulativeSpendingData} />
            )}
            {activeChartTab === "radar" && (
              <CategoryRadarChart data={categoryRadarData} />
            )}
            {activeChartTab === "savings" && (
              <IncomeVsSavingsChart data={incomeVsSavingsData} />
            )}
            {activeChartTab === "weekday" && (
              <WeekdaySpendingChart data={weekdaySpendingData} />
            )}
          </div>

          {/* Chart Descriptions */}
          <div className="mt-6 p-4 bg-gray-50 rounded-xl">
            {activeChartTab === "comparison" && (
              <p className="text-gray-600 text-sm">
                <strong>Monthly Comparison:</strong> Compare your income and
                expenses over the last 6 months to identify trends and seasonal
                patterns.
              </p>
            )}
            {activeChartTab === "cumulative" && (
              <p className="text-gray-600 text-sm">
                <strong>Cumulative Spending:</strong> Track how your spending
                accumulates over the last 30 days. Helps identify spending
                acceleration.
              </p>
            )}
            {activeChartTab === "radar" && (
              <p className="text-gray-600 text-sm">
                <strong>Spending Pattern:</strong> Compare your category
                spending between this month (blue) and last month (purple) to
                spot changes.
              </p>
            )}
            {activeChartTab === "savings" && (
              <p className="text-gray-600 text-sm">
                <strong>Income, Expenses & Savings:</strong> Visualize how much
                you're saving each month. The line shows your net savings trend.
              </p>
            )}
            {activeChartTab === "weekday" && (
              <p className="text-gray-600 text-sm">
                <strong>Spending by Weekday:</strong> See which days you tend to
                spend more. Green = below average, Red = above average spending.
              </p>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default InsightsPage;
