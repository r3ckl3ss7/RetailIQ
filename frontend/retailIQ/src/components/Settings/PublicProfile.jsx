import { useState, useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import api from "../../services/api";
import { updateUserSuccess } from "../../features/auth/authSlice";

const PublicProfile = () => {
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);

  const { user } = useSelector((state) => state.auth);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");

  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
      setAvatarUrl(user.avatar_url || "");
    }
  }, [user]);

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setNotification({
        type: "error",
        message: "Image file is too large. Max limit is 5MB.",
      });
      return;
    }

    setUploading(true);
    setNotification(null);

    try {
      const secureUrl = await uploadImageToCloudinary(file);
      setAvatarUrl(secureUrl);

      const updatedUserPayload = {
        name,
        email,
        avatar_url: secureUrl
      };

      const response = await api.patch(`/user/${user.id}`, updatedUserPayload);
      const updatedUser = response.data;

      localStorage.setItem("user", JSON.stringify(updatedUser));
      dispatch(updateUserSuccess(updatedUser));

      setNotification({
        type: "success",
        message: "Profile picture uploaded and saved successfully!",
      });
    } catch (err) {
      console.error(err);
      setNotification({
        type: "error",
        message: err.message || "Failed to upload image. Please try again.",
      });
    } finally {
      setUploading(false);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setNotification(null);

    try {
      const payload = {
        name,
        email,
        avatar_url: avatarUrl,
      };

      const response = await api.patch(`/user/${user.id}`, payload);
      const updatedUser = response.data;

      localStorage.setItem("user", JSON.stringify(updatedUser));
      dispatch(updateUserSuccess(updatedUser));

      setNotification({
        type: "success",
        message: "Public profile updated successfully!",
      });
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || "Failed to update profile. Please try again.";
      setNotification({
        type: "error",
        message: errMsg,
      });
    } finally {
      setSaving(false);
    }
  };

  const getInitials = (n) => {
    if (!n) return "U";
    return n.split(" ").map(x => x[0]).join("").toUpperCase().substring(0, 2);
  };

  return (
    <div className="public-profile-container">
      {notification && (
        <div className={`notification-toast ${notification.type}`}>
          {notification.type === "success" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          )}
          <span>{notification.message}</span>
        </div>
      )}

      <div className="public-profile-header">
        <h1 className="main-settings-title">Profile settings</h1>
      </div>

      <div className="public-profile-grid">
        <form onSubmit={handleSubmit} className="public-profile-form">
          <div className="settings-form-group">
            <label className="form-label" htmlFor="profile-name">
              Name
            </label>
            <input
              type="text"
              id="profile-name"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="settings-form-group">
            <label className="form-label" htmlFor="profile-email">
              Email address
            </label>
            <input
              type="email"
              id="profile-email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? (
              <span className="btn-loader">
                <span className="spinner" />
                Saving profile...
              </span>
            ) : (
              "Update profile"
            )}
          </button>
        </form>

        <div className="public-profile-avatar-panel">
          <label className="form-label">Profile picture</label>
          <div className="avatar-preview-container">
            <div className="avatar-preview-circle">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Avatar Preview" className="avatar-preview-img" />
              ) : (
                <span className="avatar-preview-fallback">{getInitials(name)}</span>
              )}
              {uploading && (
                <div className="avatar-uploading-overlay">
                  <div className="spinner white" />
                </div>
              )}
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleAvatarChange}
              accept="image/*"
              style={{ display: "none" }}
            />

            <button
              type="button"
              className="avatar-edit-badge-btn"
              onClick={triggerFileSelect}
              disabled={uploading}
              title="Change your avatar"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
              <span>Edit</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicProfile;
