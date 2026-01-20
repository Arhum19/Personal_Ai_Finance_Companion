import { useState, useEffect, useMemo } from "react";
import { FaPlus, FaTrash, FaEdit, FaWallet, FaCalendar } from "react-icons/fa";
import toast from "react-hot-toast";
import MainLayout from "../layouts/MainLayout";
import Pagination from "../components/Pagination";
import FilterBar from "../components/FilterBar";
import { incomeAPI } from "../services/api";
import useAppStore from "../store/appStore";

const IncomePage = () => {
  const { triggerRefresh } = useAppStore();
  const [incomes, setIncomes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Filter state
  const [filters, setFilters] = useState({
    search: "",
    minAmount: "",
    maxAmount: "",
    startDate: "",
    endDate: "",
    sortBy: "date_desc",
  });

  const [formData, setFormData] = useState({
    amount: "",
    source: "",
    date: new Date().toISOString().split("T")[0],
  });

  useEffect(() => {
    fetchIncomes();
  }, []);

  const fetchIncomes = async () => {
    setLoading(true);
    try {
      const response = await incomeAPI.getAll();
      setIncomes(response.data || []);
    } catch (error) {
      console.error("Error fetching incomes:", error);
      toast.error("Failed to load income data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    try {
      const payload = {
        amount: parseFloat(formData.amount),
        source: formData.source || null,
        date: formData.date ? new Date(formData.date).toISOString() : null,
      };

      if (editingId) {
        await incomeAPI.update(editingId, payload);
        toast.success("Income updated successfully!");
      } else {
        await incomeAPI.create(payload);
        toast.success("Income added successfully!");
      }

      resetForm();
      fetchIncomes();
      triggerRefresh(); // Trigger dashboard refresh
    } catch (error) {
      console.error("Error saving income:", error);
      toast.error(error.response?.data?.detail || "Failed to save income");
    }
  };

  const handleEdit = (income) => {
    setFormData({
      amount: income.amount.toString(),
      source: income.source || "",
      date: new Date(income.date).toISOString().split("T")[0],
    });
    setEditingId(income.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this income?")) return;

    try {
      await incomeAPI.delete(id);
      toast.success("Income deleted successfully!");
      fetchIncomes();
      triggerRefresh(); // Trigger dashboard refresh
    } catch (error) {
      console.error("Error deleting income:", error);
      toast.error("Failed to delete income");
    }
  };

  const resetForm = () => {
    setFormData({
      amount: "",
      source: "",
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

  // Filter and sort incomes
  const filteredIncomes = useMemo(() => {
    let result = [...incomes];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (inc) => inc.source && inc.source.toLowerCase().includes(searchLower)
      );
    }

    // Amount range filter
    if (filters.minAmount) {
      result = result.filter(
        (inc) => parseFloat(inc.amount) >= parseFloat(filters.minAmount)
      );
    }
    if (filters.maxAmount) {
      result = result.filter(
        (inc) => parseFloat(inc.amount) <= parseFloat(filters.maxAmount)
      );
    }

    // Date range filter
    if (filters.startDate) {
      result = result.filter(
        (inc) => new Date(inc.date) >= new Date(filters.startDate)
      );
    }
    if (filters.endDate) {
      const endDate = new Date(filters.endDate);
      endDate.setHours(23, 59, 59, 999);
      result = result.filter((inc) => new Date(inc.date) <= endDate);
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
  }, [incomes, filters]);

  // Paginated incomes
  const paginatedIncomes = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredIncomes.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredIncomes, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredIncomes.length / itemsPerPage);

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

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Income Tracker</h1>
            <p className="text-gray-600 mt-2">Manage your income sources</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 font-semibold"
          >
            <FaPlus /> {showForm ? "Cancel" : "Add Income"}
          </button>
        </div>

        {/* Income Form */}
        {showForm && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8 transform transition-all duration-300">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingId ? "Edit Income" : "Add New Income"}
            </h2>
            <form
              onSubmit={handleSubmit}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
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
                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Source
                </label>
                <input
                  type="text"
                  name="source"
                  value={formData.source}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                  placeholder="e.g., Salary, Freelance, Investment"
                />
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
                />
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
                  className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-semibold shadow-lg"
                >
                  {editingId ? "Update Income" : "Add Income"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Filter Bar */}
        <FilterBar
          onFilterChange={handleFilterChange}
          showCategoryFilter={false}
          showAmountFilter={true}
          showDateFilter={true}
          showSearch={true}
          searchPlaceholder="Search by source..."
        />

        {/* Income List */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800">Income History</h2>
            <span className="text-sm text-gray-500">
              {filteredIncomes.length} record
              {filteredIncomes.length !== 1 ? "s" : ""}
              {filters.search ||
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
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent"></div>
              <p className="mt-4 text-gray-600">Loading income data...</p>
            </div>
          ) : incomes.length === 0 ? (
            <div className="p-12 text-center">
              <FaWallet className="mx-auto text-6xl text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">No income records yet</p>
              <p className="text-gray-400 mt-2">
                Click "Add Income" to track your earnings
              </p>
            </div>
          ) : filteredIncomes.length === 0 ? (
            <div className="p-12 text-center">
              <FaWallet className="mx-auto text-6xl text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">
                No income matches your filters
              </p>
              <p className="text-gray-400 mt-2">
                Try adjusting your search criteria
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gradient-to-r from-green-50 to-green-100 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">
                        Date
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">
                        Source
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
                    {paginatedIncomes.map((income) => (
                      <tr
                        key={income.id}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <FaCalendar className="text-green-500" />
                            {new Date(income.date).toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            })}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-semibold">
                            {income.source || "Other Income"}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-green-600 font-bold text-lg">
                          +${parseFloat(income.amount).toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleEdit(income)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                              title="Edit"
                            >
                              <FaEdit />
                            </button>
                            <button
                              onClick={() => handleDelete(income.id)}
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
                  <tfoot className="bg-gradient-to-r from-green-50 to-green-100">
                    <tr>
                      <td
                        colSpan="2"
                        className="px-6 py-4 text-left font-bold text-gray-800"
                      >
                        Total (Filtered)
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-green-600 text-xl">
                        $
                        {filteredIncomes
                          .reduce((sum, inc) => sum + parseFloat(inc.amount), 0)
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
                  totalItems={filteredIncomes.length}
                  itemsPerPage={itemsPerPage}
                  onPageChange={handlePageChange}
                  onItemsPerPageChange={handleItemsPerPageChange}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default IncomePage;
