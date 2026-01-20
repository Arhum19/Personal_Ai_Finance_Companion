import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ========== AUTH ENDPOINTS ==========
export const authAPI = {
  register: (userData) => api.post("/auth/register", userData),
  login: (credentials) => {
    // Backend expects JSON with email and password
    return api.post("/auth/login", {
      email: credentials.email,
      password: credentials.password,
    });
  },
  getCurrentUser: () => api.get("/auth/me"),
};

// ========== CATEGORY ENDPOINTS ==========
export const categoryAPI = {
  getAll: () => api.get("/category/"),
  create: (data) => api.post("/category/", data),
  update: (id, data) => api.put(`/category/${id}`, data),
  delete: (id) => api.delete(`/category/${id}`),
};

// ========== INCOME ENDPOINTS ==========
export const incomeAPI = {
  getAll: (params) => api.get("/income/", { params }),
  create: (data) => api.post("/income/", data),
  update: (id, data) => api.put(`/income/${id}`, data),
  delete: (id) => api.delete(`/income/${id}`),
};

// ========== EXPENSE ENDPOINTS ==========
export const expenseAPI = {
  getAll: (params) => api.get("/expense/", { params }),
  create: (data) => api.post("/expense/", data),
  update: (id, data) => api.put(`/expense/${id}`, data),
  delete: (id) => api.delete(`/expense/${id}`),
  voiceExpense: (audioBlob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");
    return api.post("/expense/voice", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ========== GOAL ENDPOINTS ==========
export const goalAPI = {
  getAll: () => api.get("/goals/"),
  create: (data) => api.post("/goals/", data),
  update: (id, data) => api.put(`/goals/${id}`, data),
  delete: (id) => api.delete(`/goals/${id}`),
  contribute: (goalId, data) => api.post(`/goals/${goalId}/contribute`, data),
  getContributions: (goalId) => api.get(`/goals/${goalId}/contributions`),
};

// ========== INSIGHTS ENDPOINTS ==========
export const insightsAPI = {
  getSpendingInsights: () => api.get("/insights/spending"),
  whatIf: (data) => api.post("/insights/what-if", data),
  invalidateCache: () => api.post("/insights/cache/invalidate"),
};

// ========== VOICE ENDPOINTS ==========
export const voiceAPI = {
  transcribe: (audioBlob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    return api.post("/voice/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000, // 60 seconds for voice processing
    });
  },
};

// ========== BALANCE ENDPOINT ==========
export const balanceAPI = {
  get: (params) => api.get("/summary/balance", { params }),
};

export default api;
