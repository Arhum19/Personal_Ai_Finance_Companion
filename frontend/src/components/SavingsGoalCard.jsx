import React from "react";
import { FaBullseye } from "react-icons/fa";

const SavingsGoalCard = ({ goal }) => {
  // Handle null/undefined goal
  if (!goal) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 transform cursor-default group">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-gray-600 text-sm font-semibold mb-1">
              Savings Goal
            </p>
            <h3 className="text-3xl font-bold text-gray-800">No Goals</h3>
          </div>
          <div className="bg-gradient-to-br from-blue-100 to-orange-100 p-3 rounded-lg group-hover:scale-110 transition-transform duration-300">
            <FaBullseye className="text-2xl text-blue-600" />
          </div>
        </div>
        <p className="text-sm text-gray-500">
          Create a goal in Goal Planning to track your savings
        </p>
      </div>
    );
  }

  const contributed = parseFloat(goal.total_contributed || 0);
  const target = parseFloat(goal.target_amount || 0);
  const percentage = target > 0 ? (contributed / target) * 100 : 0;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 transform cursor-default group">
      {/* Header with Icon */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-gray-600 text-sm font-semibold mb-1">
            Savings Goal
          </p>
          <h3 className="text-2xl font-bold text-gray-800 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-orange-500 group-hover:bg-clip-text transition-all duration-300">
            {goal.title}
          </h3>
        </div>
        <div className="bg-gradient-to-br from-blue-100 to-orange-100 p-3 rounded-lg group-hover:scale-110 transition-transform duration-300">
          <FaBullseye className="text-2xl text-blue-600" />
        </div>
      </div>

      {/* Progress Section */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-semibold text-gray-700">Progress</span>
          <span className="text-sm font-bold text-blue-600">
            {percentage.toFixed(0)}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-orange-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(percentage, 100)}%` }}
          ></div>
        </div>

        {/* Amount Info */}
        <div className="flex justify-between items-center mt-2 text-xs text-gray-600">
          <span>{formatCurrency(contributed)}</span>
          <span>of {formatCurrency(target)}</span>
        </div>
      </div>

      {/* Remaining Amount */}
      <div className="bg-blue-50 rounded-lg p-3 text-center">
        <p className="text-xs text-gray-600 mb-1">Amount Remaining</p>
        <p className="text-lg font-bold text-blue-600">
          {formatCurrency(Math.max(0, target - contributed))}
        </p>
      </div>
    </div>
  );
};

export default SavingsGoalCard;
