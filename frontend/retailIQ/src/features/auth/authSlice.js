import { createSlice } from "@reduxjs/toolkit";
const initialState = {
  user: JSON.parse(localStorage.getItem("user")),
  token: localStorage.getItem("token"),
  isAuthenticated: !!localStorage.getItem("token"),
  loading: false,
  error: null,
};
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.loading = false;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
      state.error = null;
    },
    loginFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
    },
    updateToken: (state, action) => {
      state.token = action.payload.token;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateUserSuccess: (state, action) => {
      state.user = action.payload;
    },
  },
});
export const { loginStart, loginSuccess, loginFailure, logout, updateToken, clearError, updateUserSuccess } =
  authSlice.actions;
export default authSlice.reducer;