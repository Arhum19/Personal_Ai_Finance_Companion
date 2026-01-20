import { create } from "zustand";

const useAppStore = create((set, get) => ({
  // Dashboard Data
  balance: 0,
  monthlySpending: 0,
  savingsGoal: 0,
  savingsRate: 0,
  transactions: [],
  categoryBreakdown: [],
  trendData: [], // 30-day trend data
  allExpenses: [], // All expenses for spending trend chart
  allIncomes: [], // All incomes for spending trend chart

  // Refresh trigger - increment to force dashboard refetch
  refreshTrigger: 0,

  // Loading states
  isLoading: false,

  // Error state
  error: null,

  // Actions
  setBalance: (balance) => set({ balance }),
  setMonthlySpending: (spending) => set({ monthlySpending: spending }),
  setSavingsGoal: (goal) => set({ savingsGoal: goal }),
  setSavingsRate: (rate) => set({ savingsRate: rate }),
  setTransactions: (transactions) => set({ transactions }),
  setCategoryBreakdown: (breakdown) => set({ categoryBreakdown: breakdown }),
  setTrendData: (data) => set({ trendData: data }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  // Trigger dashboard refresh - call this after adding/editing/deleting data
  triggerRefresh: () => set({ refreshTrigger: get().refreshTrigger + 1 }),

  // Bulk set dashboard data
  setDashboardData: (data) =>
    set({
      balance: data.balance || 0,
      monthlySpending: data.monthlySpending || 0,
      savingsGoal: data.savingsGoal || 0,
      savingsRate: data.savingsRate || 0,
      transactions: data.transactions || [],
      categoryBreakdown: data.categoryBreakdown || [],
      trendData: data.trendData || [],
      allExpenses: data.allExpenses || [],
      allIncomes: data.allIncomes || [],
    }),

  // Reset all data
  resetAppData: () =>
    set({
      balance: 0,
      monthlySpending: 0,
      savingsGoal: 0,
      savingsRate: 0,
      transactions: [],
      categoryBreakdown: [],
      trendData: [],
      error: null,
    }),
}));

export default useAppStore;
