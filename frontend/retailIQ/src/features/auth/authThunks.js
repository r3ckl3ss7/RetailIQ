import api from "../../services/api";
import { loginStart, loginSuccess, loginFailure, logout } from "./authSlice";
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
export const logoutUser = () => (dispatch) => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  dispatch(logout());
};
