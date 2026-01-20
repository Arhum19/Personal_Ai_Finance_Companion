import React from "react";
import { FaArrowUp, FaArrowDown } from "react-icons/fa";

const MetricCard = ({
  title,
  value,
  icon: Icon,
  trend,
  trendPositive,
  currency = true,
  format = "default",
}) => {
  // Format value based on type
  const formatValue = () => {
    if (format === "percentage") {
      return `${value.toFixed(1)}%`;
    }
    if (currency) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }
    return value.toString();
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 transform cursor-default group">
      {/* Header with Icon */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-gray-600 text-sm font-semibold mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-gray-800 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-orange-500 group-hover:bg-clip-text transition-all duration-300">
            {formatValue()}
          </h3>
        </div>
        <div className="bg-gradient-to-br from-blue-100 to-orange-100 p-3 rounded-lg group-hover:scale-110 transition-transform duration-300">
          <Icon className="text-2xl text-blue-600" />
        </div>
      </div>

      {/* Trend Indicator */}
      {trend !== undefined && trend !== null && (
        <div
          className={`flex items-center gap-2 text-sm font-semibold ${
            trendPositive ? "text-green-600" : "text-red-600"
          }`}
        >
          {trendPositive ? (
            <FaArrowUp className="text-xs" />
          ) : (
            <FaArrowDown className="text-xs" />
          )}
          <span>{Math.abs(trend).toFixed(1)}% from last month</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
