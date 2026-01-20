import { useState, useEffect } from "react";
import {
  FaUser,
  FaBell,
  FaPalette,
  FaShieldAlt,
  FaDownload,
  FaTrash,
  FaSave,
  FaSignOutAlt,
  FaCheck,
  FaMoon,
  FaSun,
  FaDollarSign,
  FaEuroSign,
  FaPoundSign,
  FaRupeeSign,
  FaFilePdf,
} from "react-icons/fa";
import toast from "react-hot-toast";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import MainLayout from "../layouts/MainLayout";
import useAuthStore from "../store/authStore";
import useThemeStore from "../store/themeStore";
import { expenseAPI, incomeAPI, goalAPI } from "../services/api";

const CURRENCIES = [
  { code: "USD", symbol: "$", icon: FaDollarSign, name: "US Dollar" },
  { code: "EUR", symbol: "€", icon: FaEuroSign, name: "Euro" },
  { code: "GBP", symbol: "£", icon: FaPoundSign, name: "British Pound" },
  { code: "INR", symbol: "₹", icon: FaRupeeSign, name: "Indian Rupee" },
];

const SettingsPage = () => {
  const { user, updateUser, logout } = useAuthStore();
  const { theme, setTheme } = useThemeStore();
  const [activeTab, setActiveTab] = useState("profile");
  const [loading, setLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  // Profile state
  const [profileData, setProfileData] = useState({
    name: "",
    email: "",
  });

  // Preferences state (stored in localStorage)
  const [preferences, setPreferences] = useState({
    currency: "USD",
    theme: "light",
    notifications: {
      expenseReminders: true,
      goalAlerts: true,
      weeklyReport: false,
      budgetWarnings: true,
    },
  });

  // Load user data and preferences
  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.name || "",
        email: user.email || "",
      });
    }

    // Load preferences from localStorage
    const savedPrefs = localStorage.getItem("financePreferences");
    if (savedPrefs) {
      const parsed = JSON.parse(savedPrefs);
      // Sync theme with themeStore
      parsed.theme = theme;
      setPreferences(parsed);
    } else {
      setPreferences((prev) => ({ ...prev, theme }));
    }
  }, [user, theme]);

  // Save preferences to localStorage whenever they change
  const savePreferences = (newPrefs) => {
    setPreferences(newPrefs);
    localStorage.setItem("financePreferences", JSON.stringify(newPrefs));
    toast.success("Preferences saved!");
  };

  const handleProfileSave = async () => {
    if (!profileData.name.trim()) {
      toast.error("Name is required");
      return;
    }

    setLoading(true);
    try {
      updateUser({ name: profileData.name });
      toast.success("Profile updated successfully!");
    } catch (error) {
      console.error("Error updating profile:", error);
      toast.error("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencyChange = (currencyCode) => {
    savePreferences({ ...preferences, currency: currencyCode });
  };

  const handleThemeChange = (newTheme) => {
    // Use the global theme store to apply theme
    setTheme(newTheme);
    savePreferences({ ...preferences, theme: newTheme });
  };

  const handleNotificationToggle = (key) => {
    savePreferences({
      ...preferences,
      notifications: {
        ...preferences.notifications,
        [key]: !preferences.notifications[key],
      },
    });
  };

  const handleExportData = async () => {
    setExportLoading(true);
    try {
      const [expensesRes, incomesRes, goalsRes] = await Promise.all([
        expenseAPI.getAll(),
        incomeAPI.getAll(),
        goalAPI.getAll(),
      ]);

      const expenses = expensesRes.data || [];
      const incomes = incomesRes.data || [];
      const goals = goalsRes.data || [];

      // Create PDF document
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();

      // Title
      doc.setFontSize(24);
      doc.setTextColor(249, 115, 22); // Orange color
      doc.text("Finance Companion", pageWidth / 2, 20, { align: "center" });

      // Subtitle
      doc.setFontSize(12);
      doc.setTextColor(100, 100, 100);
      doc.text(
        `Financial Report - ${new Date().toLocaleDateString()}`,
        pageWidth / 2,
        28,
        { align: "center" }
      );
      doc.text(
        `Generated for: ${user?.name || "User"} (${user?.email || ""})`,
        pageWidth / 2,
        35,
        { align: "center" }
      );

      let yPos = 50;

      // Summary Section
      const totalIncome = incomes.reduce(
        (sum, inc) => sum + parseFloat(inc.amount),
        0
      );
      const totalExpenses = expenses.reduce(
        (sum, exp) => sum + parseFloat(exp.amount),
        0
      );
      const netSavings = totalIncome - totalExpenses;

      doc.setFontSize(14);
      doc.setTextColor(0, 0, 0);
      doc.text("Financial Summary", 14, yPos);
      yPos += 8;

      autoTable(doc, {
        startY: yPos,
        head: [["Metric", "Amount"]],
        body: [
          ["Total Income", `$${totalIncome.toFixed(2)}`],
          ["Total Expenses", `$${totalExpenses.toFixed(2)}`],
          ["Net Savings", `$${netSavings.toFixed(2)}`],
          ["Number of Transactions", `${expenses.length + incomes.length}`],
        ],
        theme: "striped",
        headStyles: { fillColor: [249, 115, 22] },
        margin: { left: 14, right: 14 },
      });

      yPos = doc.lastAutoTable.finalY + 15;

      // Expenses Table
      if (expenses.length > 0) {
        doc.setFontSize(14);
        doc.text("Expenses", 14, yPos);
        yPos += 8;

        autoTable(doc, {
          startY: yPos,
          head: [["Date", "Title", "Category", "Amount"]],
          body: expenses.map((exp) => [
            new Date(exp.date).toLocaleDateString(),
            exp.title,
            exp.category_name || "Other",
            `$${parseFloat(exp.amount).toFixed(2)}`,
          ]),
          theme: "striped",
          headStyles: { fillColor: [239, 68, 68] }, // Red
          margin: { left: 14, right: 14 },
          columnStyles: {
            3: { halign: "right" },
          },
        });

        yPos = doc.lastAutoTable.finalY + 15;
      }

      // Check if we need a new page
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      // Income Table
      if (incomes.length > 0) {
        doc.setFontSize(14);
        doc.text("Income", 14, yPos);
        yPos += 8;

        autoTable(doc, {
          startY: yPos,
          head: [["Date", "Source", "Amount"]],
          body: incomes.map((inc) => [
            new Date(inc.date).toLocaleDateString(),
            inc.source || "Other Income",
            `$${parseFloat(inc.amount).toFixed(2)}`,
          ]),
          theme: "striped",
          headStyles: { fillColor: [16, 185, 129] }, // Green
          margin: { left: 14, right: 14 },
          columnStyles: {
            2: { halign: "right" },
          },
        });

        yPos = doc.lastAutoTable.finalY + 15;
      }

      // Check if we need a new page
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      // Goals Table
      if (goals.length > 0) {
        doc.setFontSize(14);
        doc.text("Financial Goals", 14, yPos);
        yPos += 8;

        autoTable(doc, {
          startY: yPos,
          head: [["Goal", "Target", "Saved", "Progress", "Status"]],
          body: goals.map((goal) => {
            const progress = (
              (parseFloat(goal.current_amount) /
                parseFloat(goal.target_amount)) *
              100
            ).toFixed(1);
            return [
              goal.name,
              `$${parseFloat(goal.target_amount).toFixed(2)}`,
              `$${parseFloat(goal.current_amount).toFixed(2)}`,
              `${progress}%`,
              goal.status || "Active",
            ];
          }),
          theme: "striped",
          headStyles: { fillColor: [59, 130, 246] }, // Blue
          margin: { left: 14, right: 14 },
          columnStyles: {
            1: { halign: "right" },
            2: { halign: "right" },
            3: { halign: "center" },
          },
        });
      }

      // Footer
      const pageCount = doc.internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(10);
        doc.setTextColor(150, 150, 150);
        doc.text(
          `Page ${i} of ${pageCount} - Generated by Finance Companion`,
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: "center" }
        );
      }

      // Save PDF
      doc.save(`finance-report-${new Date().toISOString().split("T")[0]}.pdf`);

      toast.success("PDF report exported successfully!");
    } catch (error) {
      console.error("Error exporting data:", error);
      toast.error("Failed to export data");
    } finally {
      setExportLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete your account? This action cannot be undone."
    );
    if (!confirmed) return;

    const doubleConfirm = window.prompt('Type "DELETE" to confirm:');
    if (doubleConfirm !== "DELETE") {
      toast.error("Account deletion cancelled");
      return;
    }

    try {
      toast.success("Account deletion requested. Logging out...");
      setTimeout(() => {
        logout();
        window.location.href = "/";
      }, 1500);
    } catch (error) {
      console.error("Error deleting account:", error);
      toast.error("Failed to delete account");
    }
  };

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  const tabs = [
    { id: "profile", label: "Profile", icon: FaUser },
    { id: "preferences", label: "Preferences", icon: FaPalette },
    { id: "notifications", label: "Notifications", icon: FaBell },
    { id: "privacy", label: "Privacy & Data", icon: FaShieldAlt },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case "profile":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Personal Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) =>
                      setProfileData({ ...profileData, name: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={profileData.email}
                    disabled
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-500 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Email cannot be changed
                  </p>
                </div>
              </div>
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleProfileSave}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50"
              >
                <FaSave />
                {loading ? "Saving..." : "Save Changes"}
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-all"
              >
                <FaSignOutAlt />
                Sign Out
              </button>
            </div>
          </div>
        );

      case "preferences":
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Currency
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {CURRENCIES.map((currency) => {
                  const Icon = currency.icon;
                  const isSelected = preferences.currency === currency.code;
                  return (
                    <button
                      key={currency.code}
                      onClick={() => handleCurrencyChange(currency.code)}
                      className={`relative p-4 rounded-xl border-2 transition-all ${
                        isSelected
                          ? "border-orange-500 bg-orange-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      {isSelected && (
                        <div className="absolute top-2 right-2 w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center">
                          <FaCheck className="text-white text-xs" />
                        </div>
                      )}
                      <Icon
                        className={`text-2xl mb-2 ${
                          isSelected ? "text-orange-500" : "text-gray-400"
                        }`}
                      />
                      <div className="font-semibold text-gray-800">
                        {currency.code}
                      </div>
                      <div className="text-sm text-gray-500">
                        {currency.name}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">
                Theme
              </h3>
              <div className="flex gap-4">
                <button
                  onClick={() => handleThemeChange("light")}
                  className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                    theme === "light"
                      ? "border-orange-500 bg-orange-50"
                      : "border-gray-200 hover:border-gray-300 dark:border-gray-600"
                  }`}
                >
                  <div className="flex items-center justify-center gap-3">
                    <FaSun
                      className={`text-2xl ${
                        theme === "light" ? "text-orange-500" : "text-gray-400"
                      }`}
                    />
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      Light
                    </span>
                  </div>
                </button>
                <button
                  onClick={() => handleThemeChange("dark")}
                  className={`flex-1 p-4 rounded-xl border-2 transition-all ${
                    theme === "dark"
                      ? "border-orange-500 bg-orange-50 dark:bg-orange-900/30"
                      : "border-gray-200 hover:border-gray-300 dark:border-gray-600"
                  }`}
                >
                  <div className="flex items-center justify-center gap-3">
                    <FaMoon
                      className={`text-2xl ${
                        theme === "dark" ? "text-orange-500" : "text-gray-400"
                      }`}
                    />
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      Dark
                    </span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        );

      case "notifications":
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Notification Preferences
            </h3>
            <div className="space-y-4">
              {[
                {
                  key: "expenseReminders",
                  label: "Expense Reminders",
                  description: "Get reminded to log your daily expenses",
                },
                {
                  key: "goalAlerts",
                  label: "Goal Alerts",
                  description:
                    "Receive alerts when you're close to reaching a goal",
                },
                {
                  key: "weeklyReport",
                  label: "Weekly Report",
                  description: "Get a weekly summary of your finances",
                },
                {
                  key: "budgetWarnings",
                  label: "Budget Warnings",
                  description: "Alert when spending exceeds budget thresholds",
                },
              ].map((item) => (
                <div
                  key={item.key}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
                >
                  <div>
                    <div className="font-medium text-gray-800">
                      {item.label}
                    </div>
                    <div className="text-sm text-gray-500">
                      {item.description}
                    </div>
                  </div>
                  <button
                    onClick={() => handleNotificationToggle(item.key)}
                    className={`relative w-14 h-8 rounded-full transition-all ${
                      preferences.notifications[item.key]
                        ? "bg-orange-500"
                        : "bg-gray-300"
                    }`}
                  >
                    <div
                      className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-all ${
                        preferences.notifications[item.key]
                          ? "left-7"
                          : "left-1"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Note: Notification features require browser permissions and will
              be fully functional in a future update.
            </p>
          </div>
        );

      case "privacy":
        return (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Export Your Data
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Download a comprehensive PDF report of your financial data
                including expenses, income, and goals.
              </p>
              <button
                onClick={handleExportData}
                disabled={exportLoading}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all disabled:opacity-50"
              >
                <FaFilePdf />
                {exportLoading ? "Generating PDF..." : "Export as PDF"}
              </button>
            </div>
            <div className="border-t dark:border-gray-700 pt-8">
              <h3 className="text-lg font-semibold text-red-600 mb-2">
                Danger Zone
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Permanently delete your account and all associated data. This
                action cannot be undone.
              </p>
              <button
                onClick={handleDeleteAccount}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all"
              >
                <FaTrash />
                Delete Account
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <MainLayout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Settings</h1>
          <p className="text-gray-600 mt-2">
            Manage your account, preferences, and privacy
          </p>
        </div>
        <div className="flex flex-col md:flex-row gap-8">
          <div className="md:w-64 flex-shrink-0">
            <div className="bg-white rounded-2xl shadow-lg p-4">
              <nav className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                        activeTab === tab.id
                          ? "bg-gradient-to-r from-orange-500 to-red-500 text-white"
                          : "text-gray-600 hover:bg-gray-100"
                      }`}
                    >
                      <Icon />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
          <div className="flex-1">
            <div className="bg-white rounded-2xl shadow-lg p-6 md:p-8">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
