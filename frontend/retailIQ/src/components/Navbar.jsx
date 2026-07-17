import { useState, useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import { logoutUser } from "../features/auth/authThunks";
import { setSelectedBusinessId } from "../features/business/businessSlice";
const Navbar = ({ onToggleSidebar }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const dropdownRef = useRef(null);
  const { user } = useSelector((state) => state.auth);
  const { businesses, selectedBusinessId } = useSelector((state) => state.business);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const selectedBusiness = businesses.find((b) => b.id === selectedBusinessId);
  const handleLogout = () => {
    dispatch(logoutUser());
    navigate("/login", { replace: true });
  };
  const handleSelectBusiness = (id) => {
    dispatch(setSelectedBusinessId(id));
    setDropdownOpen(false);
    navigate("/dashboard");
  };
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);
  return (
    <nav className="dashboard-nav">
      <div className="nav-brand">
        {user && (
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        )}
        <Link to="/dashboard" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
          <svg
            width="28"
            height="28"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="32" height="32" rx="8" fill="#2563eb" />
            <path
              d="M8 12L16 8L24 12V20L16 24L8 20V12Z"
              stroke="white"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <path d="M16 16L24 12" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M16 16V24" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M16 16L8 12" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span className="nav-title">RetailIQ</span>
        </Link>
        {user && (
          <div className="business-selector-container" ref={dropdownRef}>
            <button
              className="business-selector-btn"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="9" />
                <rect x="14" y="3" width="7" height="5" />
                <rect x="14" y="12" width="7" height="9" />
                <rect x="3" y="16" width="7" height="5" />
              </svg>
              <span>
                {selectedBusiness ? selectedBusiness.name : "Select a Business"}
              </span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="6,9 12,15 18,9" />
              </svg>
            </button>
            {dropdownOpen && (
              <div className="business-dropdown">
                {businesses.length > 0 ? (
                  businesses.map((b) => (
                    <button
                      key={b.id}
                      className={`business-dropdown-item ${
                        b.id === selectedBusinessId ? "active" : ""
                      }`}
                      onClick={() => handleSelectBusiness(b.id)}
                    >
                      <span>{b.name}</span>
                      {b.id === selectedBusinessId && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20,6 9,17 4,12" />
                        </svg>
                      )}
                    </button>
                  ))
                ) : (
                  <div style={{ padding: "10px 14px", fontSize: "0.875rem", color: "#64748b" }}>
                    No businesses found
                  </div>
                )}
                <div className="business-dropdown-divider" />
                <button
                  className="business-dropdown-action"
                  onClick={() => {
                    setDropdownOpen(false);
                    navigate("/business");
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Create Business
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="nav-user">
        <div className="user-avatar" style={{ overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }} onClick={() => navigate("/settings")}>
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt={user.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            user?.name?.charAt(0)?.toUpperCase() || "U"
          )}
        </div>
        <span className="user-name" style={{ cursor: "pointer" }} onClick={() => navigate("/settings")}>{user?.name || "User"}</span>
        <button className="logout-btn" onClick={handleLogout}>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
            <polyline points="16,17 21,12 16,7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span>Sign out</span>
        </button>
      </div>
    </nav>
  );
};
export default Navbar;
