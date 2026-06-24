import api from "../../services/api";
import { loginStart, loginSuccess, loginFailure, logout, updateUserSuccess } from "./authSlice";

export const loginUser = (email, password) => async (dispatch) => {
  dispatch(loginStart());
  try {
    const response = await api.post("/auth/login", { email, password });
    const { access_token: token, user } = response.data;
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    dispatch(loginSuccess({ token, user }));
  } catch (err) {
    const message =
      err.response?.data?.detail || "Login failed. Please try again.";
    dispatch(loginFailure(message));
  }
};

export const registerUser = (name, email, password) => async (dispatch) => {
  dispatch(loginStart());
  try {
    await api.post("/auth/register", { name, email, password });
    dispatch(loginFailure(null)); 
    return { success: true };
  } catch (err) {
    const message =
      err.response?.data?.detail || "Registration failed. Please try again.";
    dispatch(loginFailure(message));
    return { success: false };
  }
};

export const logoutUser = () => async (dispatch) => {
  try {
    await api.post("/auth/logout");
  } catch (err) {
    console.error("Backend logout failed", err);
  }
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  dispatch(logout());
};

export const updateUserProfile = (userId, payload) => async (dispatch) => {
  try {
    const response = await api.patch(`/user/${userId}`, payload);
    const updatedUser = response.data;
    localStorage.setItem("user", JSON.stringify(updatedUser));
    dispatch(updateUserSuccess(updatedUser));
    return updatedUser;
  } catch (err) {
    const message =
      err.response?.data?.detail || "Failed to update profile. Please try again.";
    throw new Error(message);
  }
};

