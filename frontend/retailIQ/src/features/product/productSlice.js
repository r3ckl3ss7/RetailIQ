import { createSlice } from "@reduxjs/toolkit";
import {
  fetchProducts,
  postProduct,
  updateProduct,
  deleteProduct,
} from "./productThunk";
const initialState = {
  data: [],
  loading: false,
  error: null,
};
const productSlice = createSlice({
  name: "products",
  initialState,
  reducers: {
    clearProducts: (state) => {
      state.data = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload && typeof action.payload === "object" && "items" in action.payload) {
          state.data = action.payload.items || [];
          state.total = action.payload.total || 0;
        } else {
          state.data = action.payload || [];
          state.total = (action.payload || []).length;
        }
        state.error = null;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(postProduct.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(postProduct.fulfilled, (state, action) => {
        state.loading = false;
        state.data.push(action.payload);
        state.error = null;
      })
      .addCase(postProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(updateProduct.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateProduct.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.data.findIndex(
          (product) => product.id === action.payload.id
        );
        if (index !== -1) {
          state.data[index] = action.payload;
        }
        state.error = null;
      })
      .addCase(updateProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(deleteProduct.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteProduct.fulfilled, (state, action) => {
        state.loading = false;
        state.data = state.data.filter(
          (product) => product.id !== action.payload
        );
        state.error = null;
      })
      .addCase(deleteProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});
const { clearProducts } = productSlice.actions;
export default productSlice.reducer;
export { clearProducts };
