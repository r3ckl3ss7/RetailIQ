import { createSlice } from "@reduxjs/toolkit";
import { fetchDashboardData } from "./dashboardThunk";

const initialState = {
  metrics: {
    totalSales: 0.0,
    totalInvoices: 0,
    recentCustomers: 0,
  },
  revenueCompare: null,
  topProducts: [],
  lowStock: [],
  revenueTrend: [],
  invoiceBreakdown: {},
  avgOrderValue: null,
  topCustomers: [],
  profitMargins: null,
  loading: false,
  error: null,
};

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {
    clearDashboard: (state) => {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.metrics = action.payload.metrics;
        state.revenueCompare = action.payload.revenueCompare;
        state.topProducts = action.payload.topProducts;
        state.lowStock = action.payload.lowStock;
        state.revenueTrend = action.payload.revenueTrend;
        state.invoiceBreakdown = action.payload.invoiceBreakdown;
        state.avgOrderValue = action.payload.avgOrderValue;
        state.topCustomers = action.payload.topCustomers;
        state.profitMargins = action.payload.profitMargins;
        state.error = null;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to fetch dashboard metrics. Please reload the page.";
      });
  },
});

export const { clearDashboard } = dashboardSlice.actions;
export default dashboardSlice.reducer;
