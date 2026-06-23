import { createSlice } from "@reduxjs/toolkit";
import {
  fetchSessions,
  fetchChatHistory,
  sendChatMessage,
  deleteSession,
} from "./chatThunk";

const initialState = {
  messages: [],
  sessions: [],
  sessionId: null,
  loading: false,
  fetchingHistory: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    setSessionId: (state, action) => {
      state.sessionId = action.payload;
    },
    clearChat: (state) => {
      state.sessionId = null;
      state.messages = [];
      state.error = null;
    },
    optimisticUserMessage: (state, action) => {
      state.messages.push(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSessions.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchSessions.fulfilled, (state, action) => {
        state.sessions = action.payload || [];
      })
      .addCase(fetchSessions.rejected, (state, action) => {
        state.error = action.payload;
      })
      
      .addCase(fetchChatHistory.pending, (state) => {
        state.fetchingHistory = true;
        state.error = null;
      })
      .addCase(fetchChatHistory.fulfilled, (state, action) => {
        state.fetchingHistory = false;
        state.messages = action.payload || [];
      })
      .addCase(fetchChatHistory.rejected, (state, action) => {
        state.fetchingHistory = false;
        state.error = action.payload;
      })

      .addCase(sendChatMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.loading = false;
        const responseData = action.payload;
        
        if (!state.sessionId && responseData.session_id) {
          state.sessionId = responseData.session_id;
        }

        state.messages.push({
          id: responseData.id,
          sender: responseData.sender,
          message: responseData.message,
          created_at: responseData.created_at,
        });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.messages.push({
          id: Date.now(),
          sender: "assistant",
          message: "An error occurred while communicating with the AI. Please verify backend connection and try again.",
          created_at: new Date().toISOString(),
        });
      })

      .addCase(deleteSession.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteSession.fulfilled, (state, action) => {
        state.loading = false;
        const deletedId = action.payload;
        state.sessions = state.sessions.filter((s) => s.session_id !== deletedId);
        if (state.sessionId === deletedId) {
          state.sessionId = null;
          state.messages = [];
        }
      })
      .addCase(deleteSession.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setSessionId, clearChat, optimisticUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
