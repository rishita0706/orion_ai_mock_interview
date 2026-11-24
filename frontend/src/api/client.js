
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("orion_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("orion_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/api/auth/register", data),
  login: (email, password) =>
    api.post(
      "/api/auth/login",
      new URLSearchParams({ username: email, password }),
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    ),
  me: () => api.get("/api/auth/me"),
};

// ── Questions ─────────────────────────────────────────────────────────────────
export const questionsAPI = {
  getRandom: () => api.get("/api/questions/random"),
};

// ── Sessions ──────────────────────────────────────────────────────────────────
export const sessionsAPI = {
  create: () => api.post("/api/sessions/"),
  list: () => api.get("/api/sessions/"),
  get: (id) => api.get(`/api/sessions/${id}`),
  uploadAnswer: (sessionId, formData) =>
    api.post(`/api/sessions/${sessionId}/answers`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  complete: (sessionId) => api.post(`/api/sessions/${sessionId}/complete`),
};

// ── Analysis ──────────────────────────────────────────────────────────────────
export const analysisAPI = {
  get: (sessionId) => api.get(`/api/analysis/${sessionId}`),
  getHistory: () => api.get("/api/analysis/history/me"),
};

export default api;
