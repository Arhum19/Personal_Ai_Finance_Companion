import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  FaHome,
  FaWallet,
  FaCreditCard,
  FaBullseye,
  FaMicrophone,
  FaLightbulb,
  FaCog,
  FaBars,
  FaTimes,
  FaSignOutAlt,
} from "react-icons/fa";
import useAuthStore from "../store/authStore";

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const menuItems = [
    { path: "/dashboard", icon: FaHome, label: "Dashboard" },
    { path: "/income", icon: FaWallet, label: "Income" },
    { path: "/expense", icon: FaCreditCard, label: "Expense" },
    { path: "/goals", icon: FaBullseye, label: "Goals" },
    { path: "/voice", icon: FaMicrophone, label: "Voice Entry" },
    { path: "/insights", icon: FaLightbulb, label: "Insights" },
    { path: "/settings", icon: FaCog, label: "Settings" },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
        fixed top-0 left-0 h-full bg-gradient-to-b from-sky-400 to-sky-600 text-white
        w-64 transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}
      >
        {/* Header */}
        <div className="p-6 border-b border-sky-300">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-orange-200 bg-clip-text text-transparent">
              CASHDASH
            </h1>
            <button
              onClick={toggleSidebar}
              className="lg:hidden text-white hover:text-orange-300 transition"
            >
              <FaTimes size={24} />
            </button>
          </div>
        </div>

        {/* User Profile */}
        <div className="p-6 border-b border-sky-300">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-xl font-bold">
              {user?.name?.charAt(0).toUpperCase() ||
                user?.email?.charAt(0).toUpperCase() ||
                "U"}
            </div>
            <div>
              <p className="font-semibold text-white">{user?.name || "User"}</p>
              <p className="text-xs text-sky-100">
                {user?.email || "user@cashdash.com"}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 flex-1 overflow-y-auto">
          <ul className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`
                      flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200
                      ${
                        isActive
                          ? "bg-white text-sky-600 shadow-lg"
                          : "text-white hover:bg-sky-500"
                      }
                    `}
                    onClick={() => {
                      if (window.innerWidth < 1024) toggleSidebar();
                    }}
                  >
                    <Icon
                      className={`text-xl ${
                        isActive ? "text-sky-600" : "text-white"
                      }`}
                    />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-sky-300">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 px-4 py-3 rounded-lg text-white hover:bg-red-500 transition-all duration-200 w-full"
          >
            <FaSignOutAlt className="text-xl" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
