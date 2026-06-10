import { createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../services/api";
export const fetchProducts = createAsyncThunk(
  "products/fetchProducts",
  async (businessId, { rejectWithValue }) => {
    try {
      const response = await api.get("/products", {
        params: { business_id: businessId },
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
export const fetchProduct = createAsyncThunk(
  "products/fetchProduct",
  async (productId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/products/${productId}`);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
export const searchProducts = createAsyncThunk(
  "products/searchProducts",
  async ({ businessId, sku, barcode, name }, { rejectWithValue }) => {
    try {
      const response = await api.get("/products/search", {
        params: {
          business_id: businessId,
          sku,
          barcode,
          name,
        },
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
export const postProduct = createAsyncThunk(
  "products/postProduct",
  async (data, { rejectWithValue }) => {
    try {
      const response = await api.post("/products", data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
export const updateProduct = createAsyncThunk(
  "products/updateProduct",
  async ({ productId, data }, { rejectWithValue }) => {
    try {
      const response = await api.patch(`/products/${productId}`, data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
export const deleteProduct = createAsyncThunk(
  "products/deleteProduct",
  async (productId, { rejectWithValue }) => {
    try {
      await api.delete(`/products/${productId}`);
      return productId;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
