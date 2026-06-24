import { createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../services/api";


export const uploadImageThunk = createAsyncThunk(
  "upload/uploadImage",
  async ({ file, type = "avatar" }, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const endpoint = type === "logo" ? "/upload/logo" : "/upload/avatar";

      const response = await api.post(endpoint, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      const baseUrl = import.meta.env.VITE_API_URL;
      return `${baseUrl}${response.data.url}`;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
