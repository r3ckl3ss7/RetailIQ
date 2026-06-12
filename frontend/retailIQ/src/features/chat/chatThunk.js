import { createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../services/api";

export const fetchSessions = createAsyncThunk(
  "chat/fetchSessions",
  async (businessId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/ai/sessions`, {
        params: { business_id: businessId },
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);

export const fetchChatHistory = createAsyncThunk(
  "chat/fetchChatHistory",
  async ({ businessId, sessionId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/ai/history/${sessionId}`, {
        params: { business_id: businessId },
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);

export const sendChatMessage = createAsyncThunk(
  "chat/sendChatMessage",
  async ({ businessId, message, sessionId }, { rejectWithValue }) => {
    try {
      const response = await api.post(`/ai/chat?business_id=${businessId}`, {
        message,
        session_id: sessionId || null,
      });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);

export const deleteSession = createAsyncThunk(
  "chat/deleteSession",
  async ({ businessId, sessionId }, { rejectWithValue }) => {
    try {
      await api.delete(`/ai/sessions/${sessionId}`, {
        params: { business_id: businessId },
      });
      return sessionId;
    } catch (err) {
      return rejectWithValue(err.response?.data || { error: err.message });
    }
  }
);
