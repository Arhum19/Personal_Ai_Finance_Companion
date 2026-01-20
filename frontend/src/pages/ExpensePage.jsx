import { useState, useEffect, useMemo } from "react";
import {
  FaPlus,
  FaTrash,
  FaEdit,
  FaCreditCard,
  FaCalendar,
  FaMicrophone,
} from "react-icons/fa";
import toast from "react-hot-toast";
import MainLayout from "../layouts/MainLayout";
import VoiceEntry from "../components/VoiceEntry";
import Pagination from "../components/Pagination";
import FilterBar from "../components/FilterBar";
import { expenseAPI, categoryAPI } from "../services/api";
import useAppStore from "../store/appStore";

const ExpensePage = () => {
  const { triggerRefresh } = useAppStore();
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showVoiceModal, setShowVoiceModal] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Filter state
  const [filters, setFilters] = useState({
    search: "",
    category: "",
    minAmount: "",
    maxAmount: "",
    startDate: "",
    endDate: "",
    sortBy: "date_desc",
  });

  const [formData, setFormData] = useState({
    title: "",
    amount: "",
    description: "",
    category_id: "",
    date: new Date().toISOString().split("T")[0],
  });

  useEffect(() => {
    fetchExpenses();
    fetchCategories();
  }, []);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const response = await expenseAPI.getAll();
      setExpenses(response.data || []);
    } catch (error) {
      console.error("Error fetching expenses:", error);
      toast.error("Failed to load expense data");
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await categoryAPI.getAll();
      setCategories(response.data || []);
    } catch (error) {
      console.error("Error fetching categories:", error);
      toast.error("Failed to load categories");
    }
  };

  // Filter and sort expenses
  const filteredExpenses = useMemo(() => {
    let result = [...expenses];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (exp) =>
          exp.title.toLowerCase().includes(searchLower) ||
          (exp.description &&
            exp.description.toLowerCase().includes(searchLower)) ||
          (exp.category_name &&
            exp.category_name.toLowerCase().includes(searchLower))
      );
    }

    // Category filter
    if (filters.category) {
      result = result.filter(
        (exp) => exp.category_id === parseInt(filters.category)
      );
    }

    // Amount range filter
    if (filters.minAmount) {
      result = result.filter(
        (exp) => parseFloat(exp.amount) >= parseFloat(filters.minAmount)
      );
    }
    if (filters.maxAmount) {
      result = result.filter(
        (exp) => parseFloat(exp.amount) <= parseFloat(filters.maxAmount)
      );
    }

    // Date range filter
    if (filters.startDate) {
      result = result.filter(
        (exp) => new Date(exp.date) >= new Date(filters.startDate)
      );
    }
    if (filters.endDate) {
      const endDate = new Date(filters.endDate);
      endDate.setHours(23, 59, 59, 999);
      result = result.filter((exp) => new Date(exp.date) <= endDate);
    }

    // Sort
    result.sort((a, b) => {
      switch (filters.sortBy) {
        case "date_asc":
          return new Date(a.date) - new Date(b.date);
        case "date_desc":
          return new Date(b.date) - new Date(a.date);
        case "amount_asc":
          return parseFloat(a.amount) - parseFloat(b.amount);
        case "amount_desc":
          return parseFloat(b.amount) - parseFloat(a.amount);
        default:
          return new Date(b.date) - new Date(a.date);
      }
    });

    return result;
  }, [expenses, filters]);

  // Paginated expenses
  const paginatedExpenses = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredExpenses.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredExpenses, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredExpenses.length / itemsPerPage);

  // Reset to page 1 when filters change
  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (count) => {
    setItemsPerPage(count);
    setCurrentPage(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.title || !formData.amount || !formData.category_id) {
      toast.error("Please fill in all required fields");
      return;
    }

    if (parseFloat(formData.amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    try {
      const payload = {
        title: formData.title,
        amount: parseFloat(formData.amount),
        description: formData.description || null,
        category_id: parseInt(formData.category_id),
        date: formData.date ? new Date(formData.date).toISOString() : null,
      };

      if (editingId) {
        await expenseAPI.update(editingId, payload);
        toast.success("Expense updated successfully!");
      } else {
        await expenseAPI.create(payload);
        toast.success("Expense added successfully!");
      }

      resetForm();
      fetchExpenses();
      triggerRefresh(); // Trigger dashboard refresh
    } catch (error) {
      console.error("Error saving expense:", error);
      toast.error(error.response?.data?.detail || "Failed to save expense");
    }
  };

  const handleEdit = (expense) => {
    setFormData({
      title: expense.title,
      amount: expense.amount.toString(),
      description: expense.description || "",
      category_id: expense.category_id.toString(),
      date: new Date(expense.date).toISOString().split("T")[0],
    });
    setEditingId(expense.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this expense?")) return;

    try {
      await expenseAPI.delete(id);
      toast.success("Expense deleted successfully!");
      fetchExpenses();
      triggerRefresh(); // Trigger dashboard refresh
    } catch (error) {
      console.error("Error deleting expense:", error);
      toast.error("Failed to delete expense");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      amount: "",
      description: "",
      category_id: "",
      date: new Date().toISOString().split("T")[0],
    });
    setEditingId(null);
    setShowForm(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleVoiceEntry = () => {
    setShowVoiceModal(true);
  };

  const handleVoiceSuccess = () => {
    // Refresh expenses after voice entry
    fetchExpenses();
    triggerRefresh(); // Trigger dashboard refresh
  };

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-800">
              Expense Tracker
            </h1>
            <p className="text-gray-600 mt-2">
              Track your spending and stay on budget
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleVoiceEntry}
              className="flex items-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
            >
              <FaMicrophone /> Voice Entry
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
            >
              <FaPlus /> {showForm ? "Cancel" : "Add Expense"}
            </button>
          </div>
        </div>

        {/* Expense Form */}
        {showForm && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 transform transition-all duration-300">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingId ? "Edit Expense" : "Add New Expense"}
            </h2>
            <form
              onSubmit={handleSubmit}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                  placeholder="e.g., Groceries, Dinner, Uber"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Amount *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 font-bold">
                    $
                  </span>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    step="0.01"
                    min="0"
                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  name="category_id"
                  value={formData.category_id}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                  required
                >
                  <option value="">Select a category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Date
                </label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="3"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent transition"
                  placeholder="Optional notes about this expense..."
                />
              </div>

              <div className="md:col-span-2 flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition font-semibold shadow-lg"
                >
                  {editingId ? "Update Expense" : "Add Expense"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Filter Bar */}
        <FilterBar
          onFilterChange={handleFilterChange}
          categories={categories}
          showCategoryFilter={true}
          showAmountFilter={true}
          showDateFilter={true}
          showSearch={true}
          searchPlaceholder="Search expenses..."
        />

        {/* Expense List */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800">
              Expense History
            </h2>
            <span className="text-sm text-gray-500">
              {filteredExpenses.length} expense
              {filteredExpenses.length !== 1 ? "s" : ""}
              {filters.search ||
              filters.category ||
              filters.minAmount ||
              filters.maxAmount ||
              filters.startDate ||
              filters.endDate
                ? " (filtered)"
                : ""}
            </span>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-red-500 border-t-transparent"></div>
              <p className="mt-4 text-gray-600">Loading expense data...</p>
            </div>
          ) : expenses.length === 0 ? (
            <div className="p-12 text-center">
              <FaCreditCard className="mx-auto text-6xl text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">No expenses yet</p>
              <p className="text-gray-400 mt-2">
                Click "Add Expense" or use Voice Entry to start tracking
              </p>
            </div>
          ) : filteredExpenses.length === 0 ? (
            <div className="p-12 text-center">
              <FaCreditCard className="mx-auto text-6xl text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">
                No expenses match your filters
              </p>
              <p className="text-gray-400 mt-2">
                Try adjusting your search criteria
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gradient-to-r from-red-50 to-orange-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">
                        Date
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">
                        Title
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">
                        Category
                      </th>
                      <th className="px-6 py-4 text-right text-sm font-bold text-gray-700">
                        Amount
                      </th>
                      <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedExpenses.map((expense) => (
                      <tr
                        key={expense.id}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <FaCalendar className="text-red-500" />
                            {new Date(expense.date).toLocaleDateString(
                              "en-US",
                              {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                              }
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-medium text-gray-800">
                          {expense.title}
                          {expense.description && (
                            <p className="text-xs text-gray-500 mt-1">
                              {expense.description}
                            </p>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold">
                            {expense.category_name || "Uncategorized"}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-red-600 font-bold text-lg">
                          -${parseFloat(expense.amount).toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleEdit(expense)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                              title="Edit"
                            >
                              <FaEdit />
                            </button>
                            <button
                              onClick={() => handleDelete(expense.id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                              title="Delete"
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gradient-to-r from-red-50 to-orange-50">
                    <tr>
                      <td
                        colSpan="3"
                        className="px-6 py-4 text-left font-bold text-gray-800"
                      >
                        Total (Filtered)
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-red-600 text-xl">
                        $
                        {filteredExpenses
                          .reduce((sum, exp) => sum + parseFloat(exp.amount), 0)
                          .toFixed(2)}
                      </td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {/* Pagination */}
              <div className="border-t border-gray-200">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  totalItems={filteredExpenses.length}
                  itemsPerPage={itemsPerPage}
                  onPageChange={handlePageChange}
                  onItemsPerPageChange={handleItemsPerPageChange}
                />
              </div>
            </>
          )}
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

export default ExpensePage;
