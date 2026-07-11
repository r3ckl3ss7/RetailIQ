import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { loginUser, forgotPassword, resetPassword } from "../features/auth/authThunks";
import { clearError } from "../features/auth/authSlice";
const Login = () => {
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [mode, setMode] = useState("login"); // 'login', 'forgot', 'reset'
  const [forgotEmail, setForgotEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [localSuccess, setLocalSuccess] = useState("");
  const [localError, setLocalError] = useState("");

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = location.state?.message;
  const { loading, error, isAuthenticated } = useSelector(
    (state) => state.auth
  );

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    dispatch(clearError());
    setLocalSuccess("");
    setLocalError("");
  }, [dispatch, mode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(loginUser(form.email, form.password));
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setLocalSuccess("");
    const res = await dispatch(forgotPassword(forgotEmail));
    if (res.success) {
      setLocalSuccess(res.message);
      setTimeout(() => {
        setMode("reset");
      }, 1500);
    } else {
      setLocalError(res.message);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setLocalSuccess("");
    if (newPassword !== confirmNewPassword) {
      setLocalError("Passwords do not match.");
      return;
    }
    const res = await dispatch(resetPassword(forgotEmail, otp, newPassword));
    if (res.success) {
      setLocalSuccess(res.message);
      setTimeout(() => {
        setMode("login");
        setForm({ email: forgotEmail, password: "" });
      }, 2000);
    } else {
      setLocalError(res.message);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {}
        <div className="auth-brand">
          <div className="auth-logo">
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect
                width="32"
                height="32"
                rx="8"
                fill="#2563eb"
              />
              <path
                d="M8 12L16 8L24 12V20L16 24L8 20V12Z"
                stroke="white"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M16 16L24 12"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M16 16V24"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M16 16L8 12"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <h1 className="auth-title">RetailIQ</h1>
          <p className="auth-subtitle">
            {mode === "login" && "Sign in to your account"}
            {mode === "forgot" && "Recover your password"}
            {mode === "reset" && "Set a new password"}
          </p>
        </div>
        {}
        {(successMessage || localSuccess) && (
          <div className="auth-success" id="login-success">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.22 5.28a.75.75 0 10-1.06-1.06L7 8.38 5.84 7.22a.75.75 0 00-1.06 1.06l1.5 1.5a.75.75 0 001.06 0l3.88-3.5z" />
            </svg>
            <span>{successMessage || localSuccess}</span>
          </div>
        )}
        {}
        {(error || localError) && (
          <div className="auth-error" id="login-error">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="currentColor"
            >
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm-.75 4a.75.75 0 011.5 0v3a.75.75 0 01-1.5 0V5zm.75 6.25a.75.75 0 100-1.5.75.75 0 000 1.5z" />
            </svg>
            <span>{error || localError}</span>
          </div>
        )}
        {}
        {mode === "login" && (
          <form onSubmit={handleSubmit} className="auth-form" id="login-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email address
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="M22 4L12 13L2 4" />
                </svg>
                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  className="form-input"
                />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0110 0v4" />
                </svg>
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  required
                  autoComplete="current-password"
                  className="form-input"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "-8px", marginBottom: "16px" }}>
              <button
                type="button"
                className="auth-link"
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.8125rem", padding: 0 }}
                onClick={() => {
                  setForgotEmail(form.email);
                  setMode("forgot");
                }}
              >
                Forgot password?
              </button>
            </div>
            <button
              type="submit"
              id="login-submit"
              className="auth-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loader">
                  <span className="spinner" />
                  Signing in…
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>
        )}

        {mode === "forgot" && (
          <form onSubmit={handleForgotSubmit} className="auth-form" id="forgot-form">
            <div className="form-group">
              <label htmlFor="forgotEmail" className="form-label">
                Email address
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="M22 4L12 13L2 4" />
                </svg>
                <input
                  type="email"
                  id="forgotEmail"
                  placeholder="you@example.com"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  required
                  className="form-input"
                />
              </div>
            </div>
            <button
              type="submit"
              className="auth-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loader">
                  <span className="spinner" />
                  Sending OTP…
                </span>
              ) : (
                "Send Reset OTP"
              )}
            </button>
            <div style={{ display: "flex", justifyContent: "center", marginTop: "16px" }}>
              <button
                type="button"
                className="auth-link"
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.875rem" }}
                onClick={() => setMode("login")}
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}

        {mode === "reset" && (
          <form onSubmit={handleResetSubmit} className="auth-form" id="reset-form">
            <div className="form-group">
              <label htmlFor="resetOtp" className="form-label">
                Verification OTP (6-digits)
              </label>
              <div className="input-wrapper">
                <input
                  type="text"
                  id="resetOtp"
                  placeholder="123456"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  required
                  className="form-input"
                  style={{ letterSpacing: "4px", textAlign: "center", fontSize: "1.125rem", fontWeight: "600" }}
                />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="newPassword" className="form-label">
                New Password
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0110 0v4" />
                </svg>
                <input
                  type={showNewPassword ? "text" : "password"}
                  id="newPassword"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="form-input"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  aria-label={showNewPassword ? "Hide password" : "Show password"}
                >
                  {showNewPassword ? (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="confirmNewPassword" className="form-label">
                Confirm New Password
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0110 0v4" />
                </svg>
                <input
                  type={showNewPassword ? "text" : "password"}
                  id="confirmNewPassword"
                  placeholder="••••••••"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  required
                  className="form-input"
                />
              </div>
            </div>
            <button
              type="submit"
              className="auth-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loader">
                  <span className="spinner" />
                  Resetting…
                </span>
              ) : (
                "Reset Password"
              )}
            </button>
            <div style={{ display: "flex", justifyContent: "center", marginTop: "16px", gap: "10px" }}>
              <button
                type="button"
                className="auth-link"
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.875rem" }}
                onClick={handleForgotSubmit}
              >
                Resend OTP
              </button>
              <span style={{ color: "var(--slate-400)", fontSize: "0.875rem" }}>•</span>
              <button
                type="button"
                className="auth-link"
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.875rem" }}
                onClick={() => setMode("login")}
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}
        {}
        <p className="auth-footer">
          Don't have an account?{" "}
          <Link to="/register" className="auth-link">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
};
export default Login;