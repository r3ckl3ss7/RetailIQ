import { useState, useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../../features/auth/authThunks";
import PublicProfile from "./PublicProfile";
import BusinessSettings from "./BusinessSettings";


const AccountSettings = () => {
  const { user } = useSelector((state) => state.auth);
  return (
    <div className="settings-tab-content">
      <h2 className="settings-section-title">Account settings</h2>
      <div className="settings-card card-danger">
        <h3 className="card-danger-title">Delete Account</h3>
        <p className="card-danger-desc">
          Once you delete your account, there is no going back. Please be certain.
        </p>
        <button className="btn-danger" style={{ marginTop: "12px", width: "auto" }}>
          Delete your account
        </button>
      </div>
    </div>
  );
};

const AppearanceSettings = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark" || document.body.classList.contains("dark");
  });

  const [accentColor, setAccentColor] = useState(() => {
    return localStorage.getItem("accent-color") || "#008060";
  });

  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDarkMode]);

  useEffect(() => {
    document.documentElement.style.setProperty("--brand-500", accentColor);
    const darkerColor = accentColor === "#008060" ? "#006e52" : adjustColorBrightness(accentColor, -15);
    document.documentElement.style.setProperty("--brand-600", darkerColor);
    localStorage.setItem("accent-color", accentColor);
  }, [accentColor]);

  function adjustColorBrightness(col, amt) {
    let usePound = false;
    if (col[0] === "#") {
      col = col.slice(1);
      usePound = true;
    }
    let num = parseInt(col, 16);
    let r = (num >> 16) + amt;
    if (r > 255) r = 255;
    else if (r < 0) r = 0;
    let b = ((num >> 8) & 0x00ff) + amt;
    if (b > 255) b = 255;
    else if (b < 0) b = 0;
    let g = (num & 0x0000ff) + amt;
    if (g > 255) g = 255;
    else if (g < 0) g = 0;
    return (usePound ? "#" : "") + (g | (b << 8) | (r << 16)).toString(16).padStart(6, "0");
  }

  const accents = [
    { name: "Default Teal", color: "#008060" },
    { name: "Royal Blue", color: "#2563eb" },
    { name: "Vibrant Purple", color: "#7c3aed" },
    { name: "Sunset Orange", color: "#ea580c" },
    { name: "Cherry Red", color: "#dc2626" },
  ];

  return (
    <div className="settings-tab-content">
      <h2 className="settings-section-title">Appearance settings</h2>
      <p className="settings-section-subtitle">
        Customize how RetailIQ looks on your device.
      </p>

      <div className="settings-card">
        <h3 className="settings-card-title">Theme mode</h3>
        <p className="settings-card-subtitle" style={{ marginBottom: "16px" }}>
          Choose between Dark, Light, or follow your system settings.
        </p>
        <div className="theme-options-grid">
          <button
            className={`theme-option-btn light ${!isDarkMode ? "selected" : ""}`}
            onClick={() => setIsDarkMode(false)}
          >
            <div className="theme-preview-box light-preview" />
            <span>Light Mode</span>
          </button>
          <button
            className={`theme-option-btn dark ${isDarkMode ? "selected" : ""}`}
            onClick={() => setIsDarkMode(true)}
          >
            <div className="theme-preview-box dark-preview" />
            <span>Dark Mode</span>
          </button>
        </div>
      </div>

      <div className="settings-card" style={{ marginTop: "24px" }}>
        <h3 className="settings-card-title">Accent Color</h3>
        <p className="settings-card-subtitle" style={{ marginBottom: "16px" }}>
          Personalize the main highlights and button colors.
        </p>
        <div className="accent-picker-list">
          {accents.map((acc) => (
            <button
              key={acc.color}
              className={`accent-color-btn ${accentColor === acc.color ? "active" : ""}`}
              onClick={() => setAccentColor(acc.color)}
              style={{ "--preview-color": acc.color }}
              title={acc.name}
            >
              <span className="accent-color-dot" />
              <span className="accent-color-name">{acc.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

const AccessibilitySettings = () => {
  return (
    <div className="settings-tab-content">
      <h2 className="settings-section-title">Accessibility settings</h2>
      <p className="settings-section-subtitle">
        Configure accessibility adjustments for an optimized reading experience.
      </p>
      <div className="settings-card">
        <h3 className="settings-card-title">Font scale and spacing</h3>
        <div className="accessibility-row">
          <label className="checkbox-container">
            <input type="checkbox" defaultChecked />
            <span className="checkbox-checkmark" />
            <span className="checkbox-text">Enable high-contrast mode</span>
          </label>
        </div>
        <div className="accessibility-row" style={{ marginTop: "16px" }}>
          <label className="checkbox-container">
            <input type="checkbox" />
            <span className="checkbox-checkmark" />
            <span className="checkbox-text">Optimize for screen readers</span>
          </label>
        </div>
      </div>
    </div>
  );
};

const MockSettingsTab = ({ tabName }) => {
  return (
    <div className="settings-tab-content">
      <h2 className="settings-section-title">{tabName}</h2>
      <p className="settings-section-subtitle">
        Configure settings for {tabName.toLowerCase()}.
      </p>
      <div className="settings-card empty-state-card" style={{ maxWidth: "100%", margin: "0" }}>
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
        </div>
        <h3 className="empty-state-title">{tabName} Dashboard</h3>
        <p className="empty-state-description">
          The settings panel for {tabName} is fully ready for connection to backend services.
        </p>
      </div>
    </div>
  );
};

const SettingsLayout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  const { user } = useSelector((state) => state.auth);

  const [activeTab, setActiveTab] = useState("public-profile");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    dispatch(logoutUser());
    navigate("/login", { replace: true });
  };

  const getTabLabel = (id) => {
    switch (id) {
      case "public-profile":
        return "Public profile";
      case "account":
        return "Account";
      case "appearance":
        return "Appearance";
      case "accessibility":
        return "Accessibility";
      case "notifications":
        return "Notifications";
      case "billing":
        return "Billing and licensing";
      case "emails":
        return "Emails";
      case "password":
        return "Password and authentication";
      case "sessions":
        return "Sessions";
      case "ssh":
        return "SSH and GPG keys";
      case "orgs":
        return "Organizations";
      case "enterprises":
        return "Enterprises";
      case "moderation":
        return "Moderation";
      case "businesses":
        return "Business settings";
      default:
        return "Settings";

    }
  };

  const personalSettings = [
    { id: "public-profile", name: "Profile settings" },
    { id: "account", name: "Account settings" },
    { id: "appearance", name: "Appearance settings" },
    { id: "businesses", name: "Business settings" },
  ];


  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .substring(0, 2);
  };

  const handleDropdownItemClick = (tabId) => {
    setDropdownOpen(false);
    if (tabId === "signout") {
      handleLogout();
      return;
    }

    if (tabId === "profile" || tabId === "settings") {
      setActiveTab("public-profile");
    } else if (tabId === "appearance") {
      setActiveTab("appearance");
    } else {
      setActiveTab(tabId);
    }
  };

  const userAvatarUrl = user?.avatar_url || null;

  return (
    <div className="settings-layout-container">
      <header className="settings-header-bar">
        <div className="header-left">
          <button className="hamburger-btn" onClick={() => navigate("/dashboard")} title="Go to Dashboard">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <div className="header-logo" onClick={() => navigate("/dashboard")} style={{ cursor: "pointer" }}>
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="var(--brand-500)" />
              <path d="M8 12L16 8L24 12V20L16 24L8 20V12Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M16 16L24 12" stroke="white" strokeWidth="1.5" />
              <path d="M16 16V24" stroke="white" strokeWidth="1.5" />
              <path d="M16 16L8 12" stroke="white" strokeWidth="1.5" />
            </svg>
          </div>
          <span className="header-title">Settings</span>
        </div>

        <div className="header-search-bar">
          <input type="text" placeholder="Type / to search" />
        </div>

        <div className="header-right" ref={dropdownRef}>
          <button className="header-icon-btn" title="Copilot">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          </button>
          <button className="header-icon-btn" title="Notifications">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </button>
          <button className="header-icon-btn" title="Create new...">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button className="header-icon-btn" title="Issues">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </button>

          <div className="header-avatar-container">
            <button
              className="header-avatar-btn"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              aria-label="Toggle user menu"
            >
              {userAvatarUrl ? (
                <img src={userAvatarUrl} alt={user?.name} className="avatar-img" />
              ) : (
                <span className="avatar-fallback">{getInitials(user?.name)}</span>
              )}
            </button>

            {dropdownOpen && (
              <div className="profile-dropdown-menu">
                <div className="dropdown-user-header">
                  {userAvatarUrl ? (
                    <img src={userAvatarUrl} alt={user?.name} className="dropdown-avatar" />
                  ) : (
                    <span className="dropdown-avatar-fallback">{getInitials(user?.name)}</span>
                  )}
                  <div className="dropdown-user-details">
                    <span className="dropdown-username">{user?.email}</span>
                    <span className="dropdown-fullname">{user?.name}</span>
                  </div>
                </div>

                <div className="dropdown-divider" />

                <div className="dropdown-group">
                  <button className="dropdown-item" onClick={() => handleDropdownItemClick("public-profile")}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                    <span>Profile settings</span>
                  </button>
                  <button className="dropdown-item" onClick={() => handleDropdownItemClick("appearance")}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" />
                      <path d="M12 18C15.3137 18 18 15.3137 18 12C18 8.68629 15.3137 6 12 6C8.68629 6 6 8.68629 6 12C6 15.3137 8.68629 18 12 18Z" />
                    </svg>
                    <span>Appearance</span>
                  </button>
                </div>

                <div className="dropdown-divider" />

                <div className="dropdown-group">
                  <button className="dropdown-item logout" onClick={() => handleDropdownItemClick("signout")}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16,17 21,12 16,7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    <span>Sign out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="settings-body">
        <aside className="settings-sidebar">
          <div className="sidebar-account-header">
            {userAvatarUrl ? (
              <img src={userAvatarUrl} alt={user?.name} className="sidebar-header-avatar" />
            ) : (
              <span className="sidebar-header-avatar-fallback">{getInitials(user?.name)}</span>
            )}
            <div className="sidebar-header-user-info">
              <div className="sidebar-header-names">
                <span className="sidebar-header-name">{user?.name}</span>
              </div>
              <span className="sidebar-header-subtitle">Your personal account</span>
            </div>
          </div>

          <div className="sidebar-menu-divider" />

          <ul className="sidebar-section-list">
            {personalSettings.map((item) => (
              <li key={item.id}>
                <button
                  className={`sidebar-section-btn ${activeTab === item.id ? "active" : ""}`}
                  onClick={() => setActiveTab(item.id)}
                >
                  {item.name}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="settings-content-pane">
          {activeTab === "public-profile" && <PublicProfile />}
          {activeTab === "account" && <AccountSettings />}
          {activeTab === "appearance" && <AppearanceSettings />}
          {activeTab === "businesses" && <BusinessSettings />}

        </main>
      </div>
    </div>
  );
};

export default SettingsLayout;
