import { create } from "zustand";

const useThemeStore = create((set, get) => ({
  theme: localStorage.getItem("theme") || "light",

  setTheme: (theme) => {
    localStorage.setItem("theme", theme);

    // Apply theme to document
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    set({ theme });
  },

  toggleTheme: () => {
    const newTheme = get().theme === "light" ? "dark" : "light";
    get().setTheme(newTheme);
  },

  // Initialize theme on app load
  initializeTheme: () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    set({ theme: savedTheme });
  },
}));

export default useThemeStore;
