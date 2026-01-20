import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useMemo } from "react";

const SpendingTrendChart = ({ expenses = [], incomes = [] }) => {
  // Group data by month and calculate totals
  const monthlyData = useMemo(() => {
    const months = {};

    // Process incomes
    incomes.forEach((income) => {
      const date = new Date(income.date);
      const monthKey = `${date.getFullYear()}-${String(
        date.getMonth() + 1
      ).padStart(2, "0")}`;
      const monthLabel = date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });

      if (!months[monthKey]) {
        months[monthKey] = {
          key: monthKey,
          label: monthLabel,
          income: 0,
          expense: 0,
        };
      }
      months[monthKey].income += parseFloat(income.amount || 0);
    });

    // Process expenses
    expenses.forEach((expense) => {
      const date = new Date(expense.date);
      const monthKey = `${date.getFullYear()}-${String(
        date.getMonth() + 1
      ).padStart(2, "0")}`;
      const monthLabel = date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });

      if (!months[monthKey]) {
        months[monthKey] = {
          key: monthKey,
          label: monthLabel,
          income: 0,
          expense: 0,
        };
      }
      months[monthKey].expense += parseFloat(expense.amount || 0);
    });

    // Sort by date and get last 6 months
    const sortedData = Object.values(months)
      .sort((a, b) => a.key.localeCompare(b.key))
      .slice(-6)
      .map((item) => ({
        name: item.label,
        income: Math.round(item.income * 100) / 100,
        expense: Math.round(item.expense * 100) / 100,
      }));

    return sortedData;
  }, [expenses, incomes]);

  if (monthlyData.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 h-80 flex items-center justify-center">
        <p className="text-gray-500 text-center">
          No data available. Add income and expenses to see the spending
          overview.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Spending Overview</h2>
        <div className="text-sm text-gray-500">Last 6 months</div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={monthlyData}
          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e5e7eb"
            vertical={false}
          />
          <XAxis
            dataKey="name"
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            tick={{ fill: "#6b7280" }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: "12px" }}
            tick={{ fill: "#6b7280" }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
              padding: "12px",
            }}
            formatter={(value) => [
              `$${parseFloat(value).toLocaleString("en-US", {
                maximumFractionDigits: 2,
              })}`,
              "",
            ]}
            labelStyle={{ color: "#374151", fontWeight: "bold" }}
            labelFormatter={(label) => `Month: ${label}`}
          />
          <Legend
            wrapperStyle={{ paddingTop: "20px" }}
            iconType="line"
            verticalAlign="bottom"
          />
          <Line
            type="monotone"
            dataKey="income"
            stroke="#14b8a6"
            strokeWidth={3}
            dot={{ fill: "#14b8a6", r: 6 }}
            activeDot={{ r: 8, fill: "#14b8a6" }}
            name="Income"
            isAnimationActive={true}
          />
          <Line
            type="monotone"
            dataKey="expense"
            stroke="#ef4444"
            strokeWidth={3}
            dot={{ fill: "#ef4444", r: 6 }}
            activeDot={{ r: 8, fill: "#ef4444" }}
            name="Expense"
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SpendingTrendChart;
