import axios from "axios";
import store from "../app/store";
import { updateToken, logout } from "../features/auth/authSlice";
import { addToast } from "../features/toast/toastSlice";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (
        originalRequest.url.includes("/auth/refresh") ||
        originalRequest.url.includes("/auth/login")
      ) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        store.dispatch(logout());
        window.location.href = "/login";
        
        const errMsg = error.response?.data?.detail || "Session expired.";
        store.dispatch(addToast({ id: Date.now().toString(), message: errMsg, type: "error" }));

        return Promise.reject(error);
      }

      originalRequest._retry = true;
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;

      try {
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const { access_token: newAccessToken } = response.data;

        localStorage.setItem("token", newAccessToken);

        store.dispatch(updateToken({ token: newAccessToken }));

        api.defaults.headers.common["Authorization"] = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;

        localStorage.removeItem("token");
        localStorage.removeItem("user");
        store.dispatch(logout());
        window.location.href = "/login";

        const errMsg = refreshError.response?.data?.detail || "Session expired. Please log in again.";
        store.dispatch(addToast({ id: Date.now().toString(), message: errMsg, type: "error" }));

        return Promise.reject(refreshError);
      }
    }

    // Extract exact message from backend exceptions
    let message = "An unexpected error occurred.";
    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((err) => {
          const field = err.loc && err.loc.length > 0 ? err.loc[err.loc.length - 1] : "";
          return field ? `${field}: ${err.msg}` : err.msg;
        }).join(", ");
      } else if (data.message) {
        message = data.message;
      } else if (data.error) {
        message = data.error;
      }
    } else if (error.message) {
      message = error.message;
    }
    
    // Dispatch toast notification for 5 seconds
    store.dispatch(
      addToast({
        id: (Date.now() + Math.random()).toString(),
        message,
        type: "error",
      })
    );

    return Promise.reject(error);
  }
);

export default api;
