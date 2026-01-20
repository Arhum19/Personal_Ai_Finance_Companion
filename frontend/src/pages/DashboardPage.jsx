import { useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  FaWallet,
  FaChartLine,
  FaBullseye,
  FaPercentage,
  FaPlus,
  FaMicrophone,
} from "react-icons/fa";
import toast from "react-hot-toast";
import useAuthStore from "../store/authStore";
import useAppStore from "../store/appStore";
import MainLayout from "../layouts/MainLayout";
import MetricCard from "../components/MetricCard";
import SavingsGoalCard from "../components/SavingsGoalCard";
import SpendingTrendChart from "../components/SpendingTrendChart";
import VoiceEntry from "../components/VoiceEntry";
import { CategoryBreakdownChart } from "../components/Charts";
import {
  balanceAPI,
  insightsAPI,
  expenseAPI,
  incomeAPI,
  goalAPI,
} from "../services/api";

const DashboardPage = () => {
  const user = useAuthStore((state) => state.user);
  const location = useLocation(); // Track route changes
  const {
    balance,
    monthlySpending,
    savingsRate,
    savingsGoal,
    transactions,
    trendData,
    categoryBreakdown,
    allExpenses,
    allIncomes,
    isLoading,
    refreshTrigger,
    setDashboardData,
    setIsLoading,
    setError,
  } = useAppStore();

  const [monthlyTrend, setMonthlyTrend] = useState(0);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const navigate = useNavigate();

  // Refetch data when component mounts, navigating back, OR when refreshTrigger changes
  useEffect(() => {
    fetchDashboardData();
  }, [location.key, refreshTrigger]); // Re-run when route key or refreshTrigger changes

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      // Fetch balance
      const balanceRes = await balanceAPI.get();
      const balanceData = balanceRes.data || {};
      const availableToSpend = balanceData.available_to_spend || 0;
      const totalIncome = balanceData.total_income || 0;
      const totalExpense = balanceData.total_expense || 0;

      // Fetch ALL expenses and incomes for real-time calculations
      const expensesRes = await expenseAPI.getAll({ limit: 1000 });
      const allExpenses = expensesRes.data || [];

      const incomesRes = await incomeAPI.getAll({ limit: 1000 });
      const allIncomes = incomesRes.data || [];

      // Calculate monthly spending from actual expenses (real-time)
      const now = new Date();
      const currentMonth = now.getMonth();
      const currentYear = now.getFullYear();

      const monthlyExpenses = allExpenses.filter((exp) => {
        const expDate = new Date(exp.date);
        return (
          expDate.getMonth() === currentMonth &&
          expDate.getFullYear() === currentYear
        );
      });

      const realMonthlySpend = monthlyExpenses.reduce(
        (sum, exp) => sum + parseFloat(exp.amount || 0),
        0
      );

      // Generate category breakdown from actual expenses (real-time)
      const categoryMap = {};
      monthlyExpenses.forEach((exp) => {
        const catName = exp.category_name || exp.category || "Other";
        categoryMap[catName] =
          (categoryMap[catName] || 0) + parseFloat(exp.amount || 0);
      });
      const categoryData = Object.entries(categoryMap).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: value,
      }));

      // Generate real trend data from expenses (last 30 days)
      const trendData = generateRealTrendData(allExpenses);

      // Fetch insights for AI data and month comparison (can be cached)
      let monthComparison = {};
      try {
        const insightsRes = await insightsAPI.getSpendingInsights();
        const insights = insightsRes.data || {};
        monthComparison = insights.month_comparison || {};
      } catch (insightError) {
        console.log("Insights fetch skipped:", insightError);
      }

      // Fetch goals for Savings Goal display
      let savingsGoalData = null;
      try {
        const goalsRes = await goalAPI.getAll();
        const goalsArray = goalsRes.data?.goals || [];
        // Get the first goal (primary goal) if available
        if (goalsArray.length > 0) {
          savingsGoalData = goalsArray[0];
        }
      } catch (goalsError) {
        console.log("Goals fetch skipped:", goalsError);
      }

      const trend = monthComparison.percent_change || 0;
      setMonthlyTrend(trend);

      // Calculate savings rate properly: (income - expenses) / income * 100
      const savingsRateCalc =
        totalIncome > 0
          ? ((totalIncome - totalExpense) / totalIncome) * 100
          : 0;

      // Set all dashboard data with REAL-TIME values
      setDashboardData({
        balance: availableToSpend,
        monthlySpending: realMonthlySpend, // Real-time from expenses
        savingsGoal: savingsGoalData, // Fetch from goals
        savingsRate: Math.max(0, savingsRateCalc), // Ensure non-negative
        transactions: allExpenses.slice(0, 10), // Recent 10
        trendData: trendData,
        categoryBreakdown: categoryData, // Real-time from expenses
        allExpenses: allExpenses,
        allIncomes: allIncomes,
      });
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setError("Failed to load dashboard data");
      toast.error("Failed to load dashboard data");

      // Set mock data so dashboard is still visible
      setDashboardData({
        balance: 0,
        monthlySpending: 0,
        savingsGoal: null,
        savingsRate: 0,
        transactions: [],
        trendData: generateRealTrendData([]),
        categoryBreakdown: [],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateRealTrendData = (expenses) => {
    // Generate 30 days of real trend data from expenses
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);

    // Create array for last 30 days
    const dailyData = {};
    for (let i = 0; i < 30; i++) {
      const date = new Date(thirtyDaysAgo);
      date.setDate(thirtyDaysAgo.getDate() + i);
      const dateKey = date.toISOString().split("T")[0];
      dailyData[dateKey] = { date: dateKey, spending: 0 };
    }

    // Aggregate expenses by date
    expenses.forEach((expense) => {
      const expenseDate = new Date(expense.date).toISOString().split("T")[0];
      if (dailyData[expenseDate]) {
        dailyData[expenseDate].spending += parseFloat(expense.amount || 0);
      }
    });

    // Convert to array and format dates
    return Object.values(dailyData).map((item, idx) => ({
      date: `Day ${idx + 1}`,
      spending: item.spending,
    }));
  };

  const generateCategoryBreakdown = (byCategory) => {
    // Convert category object to pie chart format
    return Object.entries(byCategory || {}).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: parseFloat(value || 0),
    }));
  };

  const handleQuickAddExpense = () => {
    navigate("/expense");
  };

  const handleVoiceEntry = () => {
    setShowVoiceModal(true);
  };

  const handleVoiceSuccess = () => {
    // Refresh dashboard data after voice entry
    fetchDashboardData();
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-8">
            <div className="h-16 bg-gray-200 rounded-lg"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-2xl"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-80 bg-gray-200 rounded-2xl"></div>
              <div className="h-80 bg-gray-200 rounded-2xl"></div>
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-800">
              Welcome back, {user?.name || "User"}! 👋
            </h1>
            <p className="text-gray-600 mt-2">
              Here's an overview of your financial health
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleQuickAddExpense}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
            >
              <FaPlus /> Add Expense
            </button>
            <button
              onClick={handleVoiceEntry}
              className="flex items-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
            >
              <FaMicrophone /> Voice Entry
            </button>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Available to Spend"
            value={balance}
            icon={FaWallet}
            trend={monthlyTrend}
            trendPositive={monthlyTrend > 0}
            currency={true}
          />
          <MetricCard
            title="Monthly Spending"
            value={monthlySpending}
            icon={FaChartLine}
            trend={5.2}
            trendPositive={false}
            currency={true}
          />
          <SavingsGoalCard goal={savingsGoal} />
          <MetricCard
            title="Savings Rate"
            value={savingsRate}
            icon={FaPercentage}
            format="percentage"
            currency={false}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 gap-6 mb-8">
          <SpendingTrendChart expenses={allExpenses} incomes={allIncomes} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CategoryBreakdownChart data={categoryBreakdown} />
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-xl font-bold text-gray-800">
              Recent Transactions
            </h3>
          </div>
          <div className="overflow-x-auto">
            {transactions && transactions.length > 0 ? (
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Description
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">
                      Amount
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.slice(0, 10).map((transaction, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {new Date(transaction.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-3 text-sm">
                        <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold">
                          {transaction.category_name ||
                            transaction.category ||
                            "Uncategorized"}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-800 font-medium">
                        {transaction.title || transaction.description}
                      </td>
                      <td className="px-6 py-3 text-sm text-right text-red-600 font-bold">
                        -${parseFloat(transaction.amount || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center text-gray-500">
                No transactions yet. Start tracking your expenses!
              </div>
            )}
          </div>
        </div>

        {/* Voice Entry Modal */}
        {showVoiceModal && (
          <VoiceEntry
            onClose={() => setShowVoiceModal(false)}
            onSuccess={handleVoiceSuccess}
          />
        )}
      </div>
    </MainLayout>
  );
};

export default DashboardPage;
