import { createSlice } from "@reduxjs/toolkit";
import { uploadImageThunk } from "./uploadThunk";

const initialState = {
  url: null,
  loading: false,
  error: null,
};

const uploadSlice = createSlice({
  name: "upload",
  initialState,
  reducers: {
    clearUpload: (state) => {
      state.url = null;
      state.loading = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadImageThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadImageThunk.fulfilled, (state, action) => {
        state.loading = false;
        state.url = action.payload;
        state.error = null;
      })
      .addCase(uploadImageThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearUpload } = uploadSlice.actions;
export default uploadSlice.reducer;
