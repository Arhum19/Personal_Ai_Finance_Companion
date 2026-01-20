import { useState, useEffect } from "react";
import {
  FaPlus,
  FaTrash,
  FaBullseye,
  FaCoins,
  FaCheckCircle,
  FaInfoCircle,
  FaCalendarAlt,
  FaDollarSign,
  FaChartLine,
} from "react-icons/fa";
import toast from "react-hot-toast";
import MainLayout from "../layouts/MainLayout";
import { goalAPI } from "../services/api";

const GoalsPage = () => {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showContributeModal, setShowContributeModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);

  const [formData, setFormData] = useState({
    title: "",
    target_amount: "",
    savings_rate: "20",
  });

  const [contributeData, setContributeData] = useState({
    amount: "",
  });

  // Store the overall monthly income from the API response
  const [overallMonthlyIncome, setOverallMonthlyIncome] = useState(0);

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    setLoading(true);
    try {
      const response = await goalAPI.getAll();
      // Backend returns { goals: [...], monthly_income: ..., etc }
      const goalsData = response.data?.goals || [];
      const monthlyIncome = response.data?.monthly_income || 0;
      setGoals(Array.isArray(goalsData) ? goalsData : []);
      setOverallMonthlyIncome(parseFloat(monthlyIncome));
    } catch (error) {
      console.error("Error fetching goals:", error);
      toast.error("Failed to load goals");
      setGoals([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.title || !formData.target_amount) {
      toast.error("Please fill in all required fields");
      return;
    }

    if (parseFloat(formData.target_amount) <= 0) {
      toast.error("Target amount must be greater than 0");
      return;
    }

    try {
      const payload = {
        title: formData.title,
        target_amount: parseFloat(formData.target_amount),
        savings_rate: parseFloat(formData.savings_rate) / 100, // Convert to decimal
      };

      await goalAPI.create(payload);
      toast.success("Goal created successfully!");
      resetForm();
      fetchGoals();
    } catch (error) {
      console.error("Error creating goal:", error);
      toast.error(error.response?.data?.detail || "Failed to create goal");
    }
  };

  const handleContribute = async (e) => {
    e.preventDefault();

    if (!contributeData.amount || parseFloat(contributeData.amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    try {
      const payload = {
        amount: parseFloat(contributeData.amount),
      };

      await goalAPI.contribute(selectedGoal.id, payload);
      toast.success(
        `Contributed $${contributeData.amount} to ${selectedGoal.title}!`
      );
      setShowContributeModal(false);
      setContributeData({ amount: "" });
      fetchGoals();
    } catch (error) {
      console.error("Error contributing:", error);
      toast.error(error.response?.data?.detail || "Failed to contribute");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this goal?")) return;

    try {
      await goalAPI.delete(id);
      toast.success("Goal deleted successfully!");
      fetchGoals();
    } catch (error) {
      console.error("Error deleting goal:", error);
      toast.error("Failed to delete goal");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      target_amount: "",
      savings_rate: "20",
    });
    setShowForm(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const openContributeModal = (goal) => {
    setSelectedGoal(goal);
    setShowContributeModal(true);
  };

  const openDetailsModal = (goal) => {
    setSelectedGoal(goal);
    setShowDetailsModal(true);
  };

  const calculateProgress = (goal) => {
    const contributed = parseFloat(goal.total_contributed || 0);
    const target = parseFloat(goal.target_amount);
    return Math.min((contributed / target) * 100, 100);
  };

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Savings Goals</h1>
            <p className="text-gray-600 mt-2">
              Set targets and track your progress
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
          >
            <FaPlus /> {showForm ? "Cancel" : "New Goal"}
          </button>
        </div>

        {/* Goal Form */}
        {showForm && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 transform transition-all duration-300">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              Create New Goal
            </h2>
            <form
              onSubmit={handleSubmit}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Goal Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder="e.g., Emergency Fund, Vacation, New Laptop"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Target Amount *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 font-bold">
                    $
                  </span>
                  <input
                    type="number"
                    name="target_amount"
                    value={formData.target_amount}
                    onChange={handleChange}
                    step="0.01"
                    min="0"
                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>

              <div className="md:col-span-3">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Savings Rate: {formData.savings_rate}% of income
                </label>
                <input
                  type="range"
                  name="savings_rate"
                  value={formData.savings_rate}
                  onChange={handleChange}
                  min="1"
                  max="100"
                  className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              <div className="md:col-span-3 flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-semibold shadow-lg"
                >
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Goals Grid */}
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading goals...</p>
          </div>
        ) : goals.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <FaBullseye className="mx-auto text-6xl text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">No goals yet</p>
            <p className="text-gray-400 mt-2">
              Create your first savings goal to get started!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {goals.map((goal) => {
              const progress = calculateProgress(goal);
              const isComplete = progress >= 100;
              const contributed = parseFloat(goal.total_contributed || 0);
              const target = parseFloat(goal.target_amount);
              const remaining = target - contributed;

              return (
                <div
                  key={goal.id}
                  className={`bg-white rounded-2xl shadow-lg p-6 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 ${
                    isComplete ? "border-2 border-green-500" : ""
                  }`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-800 mb-1">
                        {goal.title}
                      </h3>
                      <p className="text-sm text-gray-500">
                        Target: ${target.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openDetailsModal(goal)}
                        className="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition"
                        title="View Details"
                      >
                        <FaInfoCircle className="text-xl" />
                      </button>
                      {isComplete && (
                        <FaCheckCircle className="text-3xl text-green-500" />
                      )}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-gray-700">
                        ${contributed.toFixed(2)} saved
                      </span>
                      <span className="text-sm font-bold text-purple-600">
                        {progress.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className={`h-3 rounded-full transition-all duration-500 ${
                          isComplete
                            ? "bg-gradient-to-r from-green-500 to-green-600"
                            : "bg-gradient-to-r from-purple-500 to-purple-600"
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="mb-4 p-3 bg-purple-50 rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Remaining:</span>
                      <span className="font-bold text-purple-700">
                        ${remaining > 0 ? remaining.toFixed(2) : "0.00"}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-gray-600">Savings Rate:</span>
                      <span className="font-bold text-purple-700">
                        {(parseFloat(goal.savings_rate) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1 pt-2 border-t border-purple-200">
                      <span className="text-gray-600">Suggested Monthly:</span>
                      <span className="font-bold text-green-600">
                        $
                        {parseFloat(
                          goal.suggested_monthly_contribution || 0
                        ).toFixed(2)}
                      </span>
                    </div>
                    {goal.months_needed > 0 && (
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-gray-600">
                          Months to Complete:
                        </span>
                        <span className="font-bold text-blue-600">
                          {goal.months_needed}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => openContributeModal(goal)}
                      className="flex-1 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition font-semibold text-sm"
                      disabled={isComplete}
                    >
                      <FaCoins /> Contribute
                    </button>
                    <button
                      onClick={() => handleDelete(goal.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                      title="Delete Goal"
                    >
                      <FaTrash />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Contribute Modal */}
        {showContributeModal && selectedGoal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full transform transition-all">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Contribute to {selectedGoal.title}
              </h2>
              <form onSubmit={handleContribute}>
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Contribution Amount
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 font-bold text-lg">
                      $
                    </span>
                    <input
                      type="number"
                      value={contributeData.amount}
                      onChange={(e) =>
                        setContributeData({ amount: e.target.value })
                      }
                      step="0.01"
                      min="0"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition text-lg"
                      placeholder="0.00"
                      required
                      autoFocus
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Remaining: $
                    {(
                      parseFloat(selectedGoal.target_amount) -
                      parseFloat(selectedGoal.total_contributed || 0)
                    ).toFixed(2)}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowContributeModal(false);
                      setContributeData({ amount: "" });
                    }}
                    className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-semibold shadow-lg"
                  >
                    Contribute
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Details Modal */}
        {showDetailsModal && selectedGoal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full transform transition-all max-h-[90vh] overflow-y-auto">
              <div className="flex items-start justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-800">
                  {selectedGoal.title}
                </h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Goal Overview */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <FaDollarSign className="text-purple-600" />
                    <span className="text-sm font-semibold text-gray-700">
                      Target Amount
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-purple-700">
                    ${parseFloat(selectedGoal?.target_amount || 0).toFixed(2)}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <FaCoins className="text-green-600" />
                    <span className="text-sm font-semibold text-gray-700">
                      Contributed
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-green-700">
                    $
                    {parseFloat(selectedGoal?.total_contributed || 0).toFixed(
                      2
                    )}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <FaChartLine className="text-blue-600" />
                    <span className="text-sm font-semibold text-gray-700">
                      Progress
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-blue-700">
                    {parseFloat(selectedGoal?.progress_percentage || 0).toFixed(
                      1
                    )}
                    %
                  </p>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <FaDollarSign className="text-orange-600" />
                    <span className="text-sm font-semibold text-gray-700">
                      Remaining
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-orange-700">
                    $
                    {parseFloat(selectedGoal?.remaining_amount || 0).toFixed(2)}
                  </p>
                </div>
              </div>

              {/* Timeline & Contribution Details */}
              <div className="space-y-4 mb-6">
                <div className="border-l-4 border-purple-500 pl-4 py-2">
                  <h3 className="font-semibold text-gray-700 mb-1">
                    Monthly Income (Current Month)
                  </h3>
                  <p className="text-lg text-gray-600">
                    $
                    {parseFloat(
                      selectedGoal?.monthly_income || overallMonthlyIncome || 0
                    ).toFixed(2)}
                  </p>
                  {parseFloat(
                    selectedGoal?.monthly_income || overallMonthlyIncome || 0
                  ) === 0 && (
                    <p className="text-sm text-orange-600 mt-1">
                      ⚠️ No income recorded for this month.{" "}
                      <a
                        href="/income"
                        className="underline text-purple-600 font-semibold"
                      >
                        Add income
                      </a>{" "}
                      to see timeline projections.
                    </p>
                  )}
                </div>

                <div className="border-l-4 border-purple-500 pl-4 py-2">
                  <h3 className="font-semibold text-gray-700 mb-1">
                    Suggested Monthly Contribution
                  </h3>
                  <p className="text-lg text-gray-600">
                    $
                    {parseFloat(
                      selectedGoal?.suggested_monthly_contribution || 0
                    ).toFixed(2)}
                    <span className="text-sm text-gray-500 ml-2">
                      (
                      {(
                        parseFloat(selectedGoal?.savings_rate || 0) * 100
                      ).toFixed(0)}
                      % of income)
                    </span>
                  </p>
                </div>

                <div className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <FaCalendarAlt className="text-blue-600" />
                    <h3 className="font-semibold text-gray-700">Timeline</h3>
                  </div>
                  <p className="text-lg text-gray-600">
                    {selectedGoal?.months_needed || 0} months
                  </p>
                  {selectedGoal?.estimated_completion_date &&
                    selectedGoal?.months_needed > 0 && (
                      <p className="text-sm text-gray-500 mt-1">
                        Est. completion:{" "}
                        {new Date(
                          selectedGoal.estimated_completion_date
                        ).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </p>
                    )}
                  {selectedGoal?.months_needed === 0 &&
                    parseFloat(
                      selectedGoal?.monthly_income || overallMonthlyIncome || 0
                    ) === 0 && (
                      <p className="text-sm text-orange-600 mt-1 font-semibold">
                        ⚠️ Add income for this month to calculate timeline
                      </p>
                    )}
                  {selectedGoal?.months_needed === 0 &&
                    parseFloat(selectedGoal?.progress_percentage || 0) >=
                      100 && (
                      <p className="text-sm text-green-600 mt-1 font-semibold">
                        🎉 Goal achieved!
                      </p>
                    )}
                </div>

                <div className="border-l-4 border-gray-400 pl-4 py-2">
                  <h3 className="font-semibold text-gray-700 mb-1">Status</h3>
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        selectedGoal?.status === "active"
                          ? "bg-green-100 text-green-800"
                          : selectedGoal?.status === "completed"
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {selectedGoal?.status || "unknown"}
                    </span>
                    {selectedGoal?.is_achievable === false && (
                      <span className="text-sm text-red-600 font-semibold">
                        ⚠️ No income recorded
                      </span>
                    )}
                  </div>
                </div>

                <div className="border-l-4 border-gray-400 pl-4 py-2">
                  <h3 className="font-semibold text-gray-700 mb-1">
                    Created On
                  </h3>
                  <p className="text-lg text-gray-600">
                    {selectedGoal?.created_at
                      ? new Date(selectedGoal.created_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          }
                        )
                      : "Not available"}
                  </p>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setShowDetailsModal(false)}
                className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition font-semibold shadow-lg"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default GoalsPage;
