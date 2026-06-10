import { createSlice } from "@reduxjs/toolkit";
const businessSlice = createSlice({
  name: "business",
  initialState: {
    businesses: [],
    selectedBusinessId: localStorage.getItem("selectedBusinessId") ? parseInt(localStorage.getItem("selectedBusinessId")) : null,
    data: null,
    loading: false,
    error: null,
  },
  reducers: {
    clearBusiness: (state) => {
      state.data = null;
      state.businesses = [];
      state.selectedBusinessId = null;
      localStorage.removeItem("selectedBusinessId");
    },
    createStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    createSuccess: (state, action) => {
      state.loading = false;
      state.data = action.payload;
      state.error = null;
      if (!state.businesses.find(b => b.id === action.payload.id)) {
        state.businesses.push(action.payload);
      }
      state.selectedBusinessId = action.payload.id;
      localStorage.setItem("selectedBusinessId", action.payload.id);
    },
    createFailure: (state, action) => {
      state.loading = false;
      state.error =
        action.payload?.error || action.payload?.detail || action.payload;
    },
    fetchStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchSuccess: (state, action) => {
      state.data = action.payload;
      state.loading = false;
      state.error = null;
    },
    fetchFailure: (state, action) => {
      state.loading = false;
      state.error =
        action.payload?.error || action.payload?.detail || action.payload;
    },
    fetchBusinessesSuccess: (state, action) => {
      state.businesses = action.payload || [];
      state.loading = false;
      state.error = null;
      if (state.businesses.length === 1) {
        state.selectedBusinessId = state.businesses[0].id;
        localStorage.setItem("selectedBusinessId", state.businesses[0].id);
      } else if (state.businesses.length > 0) {
        const stillExists = state.businesses.some((b) => b.id === state.selectedBusinessId);
        if (!stillExists) {
          state.selectedBusinessId = state.businesses[0].id;
          localStorage.setItem("selectedBusinessId", state.businesses[0].id);
        }
      } else {
        state.selectedBusinessId = null;
        localStorage.removeItem("selectedBusinessId");
      }
    },
    setSelectedBusinessId: (state, action) => {
      state.selectedBusinessId = action.payload;
      if (action.payload) {
        localStorage.setItem("selectedBusinessId", action.payload);
      } else {
        localStorage.removeItem("selectedBusinessId");
      }
    },
    updateStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    updateSuccess: (state, action) => {
      state.loading = false;
      state.data = action.payload;
      state.error = null;
      const idx = state.businesses.findIndex(b => b.id === action.payload.id);
      if (idx !== -1) {
        state.businesses[idx] = action.payload;
      }
    },
    updateFailure: (state, action) => {
      state.loading = false;
      state.error =
        action.payload?.error || action.payload?.detail || action.payload;
    },
    deleteStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    deleteSuccess: (state, action) => {
      state.loading = false;
      state.data = null;
      state.error = null;
      const deletedId = action.payload;
      state.businesses = state.businesses.filter(b => b.id !== deletedId);
      if (state.selectedBusinessId === deletedId) {
        if (state.businesses.length > 0) {
          state.selectedBusinessId = state.businesses[0].id;
          localStorage.setItem("selectedBusinessId", state.businesses[0].id);
        } else {
          state.selectedBusinessId = null;
          localStorage.removeItem("selectedBusinessId");
        }
      }
    },
    deleteFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload.error;
    },
  },
});
export const {
  clearBusiness,
  fetchStart,
  fetchFailure,
  fetchSuccess,
  createFailure,
  createStart,
  createSuccess,
  fetchBusinessesSuccess,
  setSelectedBusinessId,
  updateFailure,
  updateStart,
  updateSuccess,
  deleteFailure,
  deleteStart,
  deleteSuccess,
} = businessSlice.actions;
export default businessSlice.reducer;
