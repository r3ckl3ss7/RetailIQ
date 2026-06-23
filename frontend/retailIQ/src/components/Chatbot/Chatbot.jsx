import React, { useState, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchSessions,
  fetchChatHistory,
  sendChatMessage,
  deleteSession,
} from "../../features/chat/chatThunk";
import {
  setSessionId,
  clearChat,
  optimisticUserMessage,
} from "../../features/chat/chatSlice";
import "./Chatbot.css";

const Chatbot = () => {
  const dispatch = useDispatch();

  const businessId = useSelector((state) => state.business.selectedBusinessId);
  const messages = useSelector((state) => state.chat.messages);
  const sessionId = useSelector((state) => state.chat.sessionId);
  const sessions = useSelector((state) => state.chat.sessions);
  const loading = useSelector((state) => state.chat.loading);
  const fetchingHistory = useSelector((state) => state.chat.fetchingHistory);

  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, loading]);

  useEffect(() => {
    if (businessId) {
      dispatch(fetchSessions(businessId));
      dispatch(clearChat());
    } else {
      dispatch(clearChat());
    }
  }, [businessId, dispatch]);

  useEffect(() => {
    if (businessId && sessionId) {
      dispatch(fetchChatHistory({ businessId, sessionId }));
    } else {
      if (!sessionId) {
        dispatch(clearChat());
      }
    }
  }, [sessionId, businessId, dispatch]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !businessId) return;

    const userText = input;
    setInput("");

    dispatch(
      optimisticUserMessage({
        id: Date.now(),
        sender: "user",
        message: userText,
        created_at: new Date().toISOString(),
      })
    );

    dispatch(sendChatMessage({ businessId, message: userText, sessionId }))
      .unwrap()
      .then(() => {
        dispatch(fetchSessions(businessId));
      });
  };

  const handleNewChat = () => {
    dispatch(clearChat());
  };

  const handleDeleteSession = () => {
    if (!sessionId || !businessId) return;
    if (!window.confirm("Are you sure you want to delete this chat session history?")) return;

    dispatch(deleteSession({ businessId, sessionId }));
  };

  const renderMessageContent = (content) => {
    if (!content) return "";

    const codeBlockRegex = /```(sql|javascript|python|json|html|css)?\n([\s\S]*?)\n```/g;
    const elements = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const textBefore = content.substring(lastIndex, match.index);
      if (textBefore) {
        elements.push(<span key={`text-${lastIndex}`}>{textBefore}</span>);
      }

      const language = match[1] || "code";
      const code = match[2];
      elements.push(
        <pre key={`code-${match.index}`}>
          <code className={`language-${language}`}>{code}</code>
        </pre>
      );

      lastIndex = codeBlockRegex.lastIndex;
    }

    const textAfter = content.substring(lastIndex);
    if (textAfter) {
      elements.push(<span key={`text-${lastIndex}`}>{textAfter}</span>);
    }

    return elements.length > 0 ? elements : content;
  };

  const formatTime = (isoString) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="chatbot-container">
      <button className="chatbot-toggle-btn" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        )}
      </button>

      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="chatbot-header-top">
              <div className="chatbot-header-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
                RetailIQ Query Assistant
              </div>
              <div className="chatbot-header-actions">
                <button className="chatbot-header-btn" title="Start New Chat" onClick={handleNewChat}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5v14" /></svg>
                </button>
                {sessionId && (
                  <button className="chatbot-header-btn" title="Delete Current Session" onClick={handleDeleteSession}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2M10 11v6M14 11v6" /></svg>
                  </button>
                )}
                <button className="chatbot-header-btn" title="Close" onClick={() => setIsOpen(false)}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6" /></svg>
                </button>
              </div>
            </div>

            {sessions.length > 0 && (
              <div className="chatbot-session-row">
                <select
                  className="chatbot-session-select"
                  value={sessionId || ""}
                  onChange={(e) => dispatch(setSessionId(e.target.value || null))}
                >
                  <option value="">-- Start Fresh / Select Conversation --</option>
                  {sessions.map((s) => (
                    <option key={s.session_id} value={s.session_id}>
                      {s.last_message ? s.last_message.substring(0, 32) + "..." : `Session ${s.session_id.substring(0, 8)}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="chatbot-messages">
            {!businessId ? (
              <div className="chatbot-empty">
                <svg className="chatbot-empty-icon" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01" /></svg>
                <div className="chatbot-empty-text">
                  Please select or create a Business profile first to activate the query chatbot.
                </div>
              </div>
            ) : fetchingHistory ? (
              <div className="chatbot-empty">
                <div className="chatbot-typing-bubble">
                  <div className="chatbot-typing-dot"></div>
                  <div className="chatbot-typing-dot"></div>
                  <div className="chatbot-typing-dot"></div>
                </div>
                <div className="chatbot-empty-text">Loading chat history...</div>
              </div>
            ) : messages.length === 0 ? (
              <div className="chatbot-empty">
                <svg className="chatbot-empty-icon" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 0 1 7.54 16.59L21 22l-5.41-1.46A10 10 0 1 1 12 2z" /></svg>
                <div className="chatbot-empty-text font-semibold">
                  Ask me anything about your business!
                </div>
                <div className="chatbot-empty-text text-xs">
                  Examples:
                  <br />
                  • "What products do we sell?"
                  <br />
                  • "Show me recent invoices."
                  <br />• "Which product has the lowest stock?"
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div key={m.id} className={`chatbot-msg-wrapper ${m.sender}`}>
                  <div className="chatbot-msg-bubble">
                    {renderMessageContent(m.message)}
                  </div>
                  <span className="chatbot-msg-time">
                    {formatTime(m.created_at)}
                  </span>
                </div>
              ))
            )}

            {loading && (
              <div className="chatbot-msg-wrapper assistant">
                <div className="chatbot-msg-bubble chatbot-typing-bubble">
                  <div className="chatbot-typing-dot"></div>
                  <div className="chatbot-typing-dot"></div>
                  <div className="chatbot-typing-dot"></div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form className="chatbot-input-container" onSubmit={handleSend}>
            <input
              type="text"
              className="chatbot-input"
              placeholder={businessId ? "Type your query..." : "Please select business..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading || !businessId}
            />
            <button
              type="submit"
              className="chatbot-send-btn"
              disabled={loading || !input.trim() || !businessId}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default Chatbot;
