import { createSlice } from "@reduxjs/toolkit";

const toastSlice = createSlice({
  name: "toast",
  initialState: {
    toasts: [],
  },
  reducers: {
    addToast: (state, action) => {
      const message = action.payload.message || "An unexpected error occurred.";
      const type = action.payload.type || "error";
      const exists = state.toasts.some(t => t.message === message && t.type === type);
      if (exists) return;

      state.toasts.push({
        id: action.payload.id || Date.now().toString() + Math.random().toString(),
        message,
        type,
      });
    },
    removeToast: (state, action) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
  },
});

export const { addToast, removeToast } = toastSlice.actions;
export default toastSlice.reducer;
