import { useState, useEffect } from "react";
import {
  FaCheck,
  FaTimes,
  FaEdit,
  FaDollarSign,
  FaTag,
  FaCalendarAlt,
  FaShoppingCart,
  FaMoneyBillWave,
  FaBullseye,
  FaPiggyBank,
  FaSpinner,
} from "react-icons/fa";
import toast from "react-hot-toast";
import { expenseAPI, incomeAPI, goalAPI, categoryAPI } from "../services/api";

/**
 * VoiceConfirmation Modal
 * Displays parsed voice data and allows user to edit before saving
 */
const VoiceConfirmation = ({
  parsedData,
  transcribedText,
  onConfirm,
  onCancel,
  onRetry,
}) => {
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({});
  const [categories, setCategories] = useState([]);
  const [goals, setGoals] = useState([]);

  useEffect(() => {
    // Initialize form data from parsed data
    setFormData({
      type: parsedData.type,
      amount: parsedData.amount || "",
      title: parsedData.title || "",
      category: parsedData.category || "",
      category_id: parsedData.category_id || null,
      source: parsedData.source || "",
      description: parsedData.description || transcribedText,
      date: parsedData.date
        ? parsedData.date.split("T")[0]
        : new Date().toISOString().split("T")[0],
      savings_rate: parsedData.savings_rate || 0.2,
      goal_id: parsedData.goal_id || null,
      goal_name: parsedData.goal_name || "",
    });

    // Use available categories from parsed data or fetch
    if (parsedData.available_categories) {
      setCategories(parsedData.available_categories);
    } else {
      fetchCategories();
    }

    // Use available goals from parsed data or fetch
    if (parsedData.available_goals) {
      setGoals(parsedData.available_goals);
    } else if (parsedData.type === "contribution") {
      fetchGoals();
    }
  }, [parsedData]);

  const fetchCategories = async () => {
    try {
      const response = await categoryAPI.getAll();
      setCategories(response.data || []);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const fetchGoals = async () => {
    try {
      const response = await goalAPI.getAll();
      setGoals(response.data?.goals || []);
    } catch (error) {
      console.error("Error fetching goals:", error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleConfirm = async () => {
    setSaving(true);

    try {
      let response;
      const { type } = formData;

      if (type === "expense") {
        // Find category_id if category name is selected
        let categoryId = formData.category_id;
        if (!categoryId && formData.category) {
          const cat = categories.find(
            (c) => c.name.toLowerCase() === formData.category.toLowerCase()
          );
          categoryId = cat?.id;
        }

        // If category still not found, create it automatically
        if (!categoryId && formData.category) {
          try {
            const newCategoryResponse = await categoryAPI.create({
              name: formData.category,
            });
            categoryId = newCategoryResponse.data.id;
            toast.success(`Created category: ${formData.category}`);
          } catch (categoryError) {
            console.error("Error creating category:", categoryError);
            toast.error("Could not create category. Please try again.");
            setSaving(false);
            return;
          }
        }

        if (!categoryId) {
          toast.error("Please select a valid category");
          setSaving(false);
          return;
        }

        response = await expenseAPI.create({
          title: formData.title || "Voice Expense",
          amount: parseFloat(formData.amount),
          category_id: categoryId,
          description: formData.description,
          date: formData.date,
        });
        toast.success("Expense added successfully! 🎉");
      } else if (type === "income") {
        response = await incomeAPI.create({
          source: formData.source || "Voice Income",
          amount: parseFloat(formData.amount),
          description: formData.description,
          date: formData.date,
        });
        toast.success("Income added successfully! 💰");
      } else if (type === "goal") {
        response = await goalAPI.create({
          title: formData.title || "New Goal",
          target_amount: parseFloat(formData.amount),
          savings_rate: parseFloat(formData.savings_rate),
        });
        toast.success("Goal created successfully! 🎯");
      } else if (type === "contribution") {
        // Find goal_id if goal name is provided
        let goalId = formData.goal_id;
        if (!goalId && formData.goal_name) {
          const goal = goals.find((g) =>
            g.title.toLowerCase().includes(formData.goal_name.toLowerCase())
          );
          goalId = goal?.id;
        }

        if (!goalId) {
          toast.error("Please select a valid goal");
          setSaving(false);
          return;
        }

        response = await goalAPI.contribute(goalId, {
          amount: parseFloat(formData.amount),
        });
        toast.success("Contribution added successfully! 🐷");
      }

      onConfirm(response?.data);
    } catch (error) {
      console.error("Error saving:", error);
      toast.error(
        error.response?.data?.detail || "Failed to save. Please try again."
      );
    } finally {
      setSaving(false);
    }
  };

  const getTypeIcon = () => {
    switch (formData.type) {
      case "expense":
        return <FaShoppingCart className="text-red-500" />;
      case "income":
        return <FaMoneyBillWave className="text-green-500" />;
      case "goal":
        return <FaBullseye className="text-purple-500" />;
      case "contribution":
        return <FaPiggyBank className="text-blue-500" />;
      default:
        return <FaDollarSign className="text-gray-500" />;
    }
  };

  const getTypeColor = () => {
    switch (formData.type) {
      case "expense":
        return "from-red-500 to-orange-500";
      case "income":
        return "from-green-500 to-emerald-500";
      case "goal":
        return "from-purple-500 to-pink-500";
      case "contribution":
        return "from-blue-500 to-cyan-500";
      default:
        return "from-gray-500 to-gray-600";
    }
  };

  const getTypeBg = () => {
    switch (formData.type) {
      case "expense":
        return "bg-red-50 border-red-200";
      case "income":
        return "bg-green-50 border-green-200";
      case "goal":
        return "bg-purple-50 border-purple-200";
      case "contribution":
        return "bg-blue-50 border-blue-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-lg w-full transform transition-all max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div
            className={`p-4 rounded-2xl bg-gradient-to-br ${getTypeColor()} text-white`}
          >
            {getTypeIcon()}
            <span className="text-2xl">{getTypeIcon()}</span>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-800 capitalize">
              {formData.type} Detected
            </h2>
            <p className="text-gray-500">Review and confirm</p>
          </div>
        </div>

        {/* Transcribed Text */}
        <div className={`p-4 rounded-xl border-2 mb-6 ${getTypeBg()}`}>
          <p className="text-sm font-semibold text-gray-600 mb-1">
            🎙️ What you said:
          </p>
          <p className="text-gray-800 italic">"{transcribedText}"</p>
        </div>

        {/* Parsed Data Display / Edit Form */}
        <div className="space-y-4 mb-6">
          {/* Amount */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              <FaDollarSign className="inline mr-1" />
              {formData.type === "goal" ? "Target Amount" : "Amount"}
            </label>
            {editMode ? (
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                step="0.01"
                min="0"
              />
            ) : (
              <p className="text-2xl font-bold text-gray-800">
                ${parseFloat(formData.amount || 0).toFixed(2)}
              </p>
            )}
          </div>

          {/* Type-specific fields */}
          {formData.type === "expense" && (
            <>
              {/* Title */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  <FaTag className="inline mr-1" /> Title
                </label>
                {editMode ? (
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="text-lg text-gray-800">{formData.title}</p>
                )}
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Category
                </label>
                {editMode ? (
                  <select
                    name="category_id"
                    value={formData.category_id || ""}
                    onChange={(e) => {
                      const selectedCat = categories.find(
                        (c) => c.id === parseInt(e.target.value)
                      );
                      setFormData((prev) => ({
                        ...prev,
                        category_id: parseInt(e.target.value),
                        category: selectedCat?.name || "",
                      }));
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select Category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name.charAt(0).toUpperCase() + cat.name.slice(1)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-lg text-gray-800 capitalize">
                    {formData.category || "Not detected"}
                  </p>
                )}
              </div>
            </>
          )}

          {formData.type === "income" && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Source
              </label>
              {editMode ? (
                <input
                  type="text"
                  name="source"
                  value={formData.source}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-lg text-gray-800">{formData.source}</p>
              )}
            </div>
          )}

          {formData.type === "goal" && (
            <>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Goal Title
                </label>
                {editMode ? (
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="text-lg text-gray-800">{formData.title}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Savings Rate:{" "}
                  {(parseFloat(formData.savings_rate || 0.2) * 100).toFixed(0)}%
                </label>
                {editMode && (
                  <input
                    type="range"
                    name="savings_rate"
                    value={formData.savings_rate * 100}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        savings_rate: parseFloat(e.target.value) / 100,
                      }))
                    }
                    min="1"
                    max="100"
                    className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                  />
                )}
              </div>
            </>
          )}

          {formData.type === "contribution" && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Goal
              </label>
              {editMode ? (
                <select
                  name="goal_id"
                  value={formData.goal_id || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      goal_id: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Goal</option>
                  {goals.map((goal) => (
                    <option key={goal.id} value={goal.id}>
                      {goal.title}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-lg text-gray-800 capitalize">
                  {parsedData.goal_title ||
                    formData.goal_name ||
                    "Not detected"}
                </p>
              )}
            </div>
          )}

          {/* Date (for expense and income) */}
          {(formData.type === "expense" || formData.type === "income") && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                <FaCalendarAlt className="inline mr-1" /> Date
              </label>
              {editMode ? (
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-lg text-gray-800">
                  {new Date(formData.date).toLocaleDateString("en-US", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={saving}
            className="flex-1 px-4 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition font-semibold disabled:opacity-50"
          >
            <FaTimes className="inline mr-2" />
            Cancel
          </button>

          <button
            onClick={() => setEditMode(!editMode)}
            disabled={saving}
            className="px-4 py-3 border-2 border-blue-500 text-blue-600 rounded-xl hover:bg-blue-50 transition font-semibold disabled:opacity-50"
          >
            <FaEdit className="inline mr-1" />
            {editMode ? "Preview" : "Edit"}
          </button>

          <button
            onClick={handleConfirm}
            disabled={saving || !formData.amount}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r ${getTypeColor()} text-white rounded-xl transition font-semibold shadow-lg hover:shadow-xl disabled:opacity-50`}
          >
            {saving ? (
              <>
                <FaSpinner className="animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <FaCheck />
                Confirm
              </>
            )}
          </button>
        </div>

        {/* Retry Button */}
        <button
          onClick={onRetry}
          disabled={saving}
          className="w-full mt-4 px-4 py-2 text-gray-500 hover:text-gray-700 transition text-sm"
        >
          🎤 Not what you meant? Try recording again
        </button>
      </div>
    </div>
  );
};

export default VoiceConfirmation;
