import { useState, useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  fetch_user_businesses,
  create_business,
  update_business,
  delete_business,
} from "../../features/business/businessThunk";
import { setSelectedBusinessId } from "../../features/business/businessSlice";
import {
  validateField,
  validateForm,
  hasErrors,
  BUSINESS_RULES,
} from "../../utils/formValidation";
import { uploadImage } from "../../services/upload";

const BusinessSettings = () => {
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);

  const { user } = useSelector((state) => state.auth);
  const { businesses, selectedBusinessId, loading, error } = useSelector(
    (state) => state.business
  );

  const [view, setView] = useState("list");
  const [editingBusiness, setEditingBusiness] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    gst_number: "",
    phone: "",
    email: "",
    address: "",
    city: "",
    state: "",
    country: "India",
    postal_code: "",
    logo_url: "",
    invoice_prefix: "INV",
    currency: "INR",
    timezone: "Asia/Kolkata",
  });

  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [logoUploading, setLogoUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (user?.id) {
      dispatch(fetch_user_businesses(user.id));
    }
  }, [dispatch, user?.id]);

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleOpenCreate = () => {
    setFormData({
      name: "",
      gst_number: "",
      phone: "",
      email: "",
      address: "",
      city: "",
      state: "",
      country: "India",
      postal_code: "",
      logo_url: "",
      invoice_prefix: "INV",
      currency: "INR",
      timezone: "Asia/Kolkata",
    });
    setErrors({});
    setTouched({});
    setView("create");
    setEditingBusiness(null);
  };

  const handleOpenEdit = (business) => {
    setEditingBusiness(business);
    setFormData({
      name: business.name || "",
      gst_number: business.gst_number || "",
      phone: business.phone || "",
      email: business.email || "",
      address: business.address || "",
      city: business.city || "",
      state: business.state || "",
      country: business.country || "India",
      postal_code: business.postal_code || "",
      logo_url: business.logo_url || "",
      invoice_prefix: business.invoice_prefix || "INV",
      currency: business.currency || "INR",
      timezone: business.timezone || "Asia/Kolkata",
    });
    setErrors({});
    setTouched({});
    setView("edit");
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (touched[name]) {
      const fieldError = validateField(value, BUSINESS_RULES[name]);
      setErrors((prev) => {
        const next = { ...prev };
        if (fieldError) next[name] = fieldError;
        else delete next[name];
        return next;
      });
    }
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    const fieldError = validateField(value, BUSINESS_RULES[name]);
    setErrors((prev) => {
      const next = { ...prev };
      if (fieldError) next[name] = fieldError;
      else delete next[name];
      return next;
    });
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setNotification({
        type: "error",
        message: "Logo image is too large. Max limit is 5MB.",
      });
      return;
    }

    setLogoUploading(true);
    try {
      const secureUrl = await uploadImage(file, "logo");
      setFormData((prev) => ({ ...prev, logo_url: secureUrl }));
      setNotification({
        type: "success",
        message: "Logo uploaded successfully!",
      });
    } catch (err) {
      console.error(err);
      setNotification({
        type: "error",
        message: err.message || "Failed to upload logo image.",
      });
    } finally {
      setLogoUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const allTouched = {};
    Object.keys(BUSINESS_RULES).forEach((k) => (allTouched[k] = true));
    setTouched(allTouched);

    const formErrors = validateForm(formData, BUSINESS_RULES);
    setErrors(formErrors);

    if (hasErrors(formErrors)) {
      setNotification({
        type: "error",
        message: "Please correct the errors in the form.",
      });
      return;
    }

    setSubmitting(true);
    try {
      if (view === "create") {
        await dispatch(create_business(formData));
        setNotification({
          type: "success",
          message: "Business profile created successfully!",
        });
      } else {
        await dispatch(update_business(formData, editingBusiness.id));
        setNotification({
          type: "success",
          message: "Business profile updated successfully!",
        });
      }
      setView("list");
    } catch (err) {
      console.error(err);
      setNotification({
        type: "error",
        message: "Operation failed. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (businessId) => {
    try {
      await dispatch(delete_business(businessId));
      setNotification({
        type: "success",
        message: "Business profile deleted successfully!",
      });
      setDeletingId(null);
    } catch (err) {
      console.error(err);
      setNotification({
        type: "error",
        message: "Failed to delete business. Please try again.",
      });
    }
  };

  const handleSetActive = (businessId) => {
    dispatch(setSelectedBusinessId(businessId));
    setNotification({
      type: "success",
      message: "Active business updated successfully!",
    });
  };

  const getInitials = (n) => {
    if (!n) return "B";
    return n
      .split(" ")
      .map((x) => x[0])
      .join("")
      .toUpperCase()
      .substring(0, 2);
  };

  const inputClass = (fieldName, base = "form-input") => {
    return `${base}${touched[fieldName] && errors[fieldName] ? " invalid" : ""}`;
  };

  return (
    <div className="settings-tab-content">
      {notification && (
        <div className={`notification-toast ${notification.type}`} style={{ zIndex: 1100 }}>
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

      {deletingId && (
        <div className="modal-overlay" style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div className="settings-card" style={{ maxWidth: "440px", width: "100%", margin: "0 16px" }}>
            <h3 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "12px", color: "var(--slate-900)" }}>Delete Business</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--slate-500)", marginBottom: "20px" }}>
              Are you sure you want to delete this business profile? All products, inventories, and invoices under this business will be permanently deleted. This action cannot be undone.
            </p>
            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
              <button className="btn-secondary" onClick={() => setDeletingId(null)}>Cancel</button>
              <button className="btn-danger" onClick={() => handleDelete(deletingId)}>Delete Permanently</button>
            </div>
          </div>
        </div>
      )}

      <div className="public-profile-header">
        <h1 className="main-settings-title">Business settings</h1>
        {view === "list" && (
          <button className="btn-primary" style={{ width: "auto" }} onClick={handleOpenCreate}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: "4px" }}>
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New business
          </button>
        )}
      </div>

      <p className="settings-section-subtitle">
        Manage your business profiles, GST details, locations, and default invoicing settings.
      </p>

      {error && view === "list" && (
        <div className="auth-error" style={{ marginBottom: "20px" }}>
          <span>{typeof error === "string" ? error : "An error occurred with business services."}</span>
        </div>
      )}

      {view === "list" && (
        <div className="businesses-list" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {loading && businesses.length === 0 ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "40px" }}>
              <span className="spinner" style={{ borderColor: "var(--brand-500) transparent transparent transparent" }} />
            </div>
          ) : businesses.length === 0 ? (
            <div className="settings-card empty-state-card" style={{ maxWidth: "100%", margin: "0" }}>
              <div className="empty-state-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <h3 className="empty-state-title">No businesses found</h3>
              <p className="empty-state-description">
                You haven't added any businesses yet. Create a business profile to start managing invoices and inventories.
              </p>
              <button className="btn-primary" style={{ width: "auto" }} onClick={handleOpenCreate}>
                Set up first business
              </button>
            </div>
          ) : (
            businesses.map((business) => (
              <div
                key={business.id}
                className={`settings-card ${business.id === selectedBusinessId ? "active-business-card" : ""}`}
                style={{
                  borderLeft: business.id === selectedBusinessId ? "4px solid var(--brand-500)" : "1px solid #30363d",
                  position: "relative"
                }}
              >
                <div className="flex-between" style={{ gap: "16px", flexWrap: "wrap" }}>
                  <div className="flex-gap-2" style={{ alignItems: "flex-start", gap: "16px" }}>
                    <div style={{
                      width: "48px",
                      height: "48px",
                      borderRadius: "6px",
                      backgroundColor: "var(--brand-100)",
                      color: "var(--brand-700)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "1.125rem",
                      fontWeight: "700",
                      flexShrink: 0,
                      overflow: "hidden",
                      border: "1px solid #30363d"
                    }}>
                      {business.logo_url ? (
                        <img src={business.logo_url} alt={business.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      ) : (
                        getInitials(business.name)
                      )}
                    </div>
                    <div>
                      <div className="flex-gap-2" style={{ flexWrap: "wrap" }}>
                        <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "var(--slate-900)" }}>{business.name}</h3>
                        {business.id === selectedBusinessId && (
                          <span className="badge badge-success" style={{ fontSize: "0.6875rem", padding: "2px 6px" }}>Active</span>
                        )}
                      </div>
                      <p style={{ fontSize: "0.8125rem", color: "var(--slate-500)", marginTop: "4px" }}>
                        {business.city ? `${business.city}, ` : ""}{business.state ? `${business.state}, ` : ""}{business.country || "India"}
                      </p>
                      <div style={{ display: "flex", gap: "12px", marginTop: "8px", flexWrap: "wrap", fontSize: "0.75rem", color: "var(--slate-400)" }}>
                        {business.gst_number && <span>GST: <strong>{business.gst_number}</strong></span>}
                        {business.email && <span>Email: {business.email}</span>}
                        {business.phone && <span>Phone: {business.phone}</span>}
                      </div>
                    </div>
                  </div>

                  <div className="flex-gap-2" style={{ marginLeft: "auto" }}>
                    {business.id !== selectedBusinessId && (
                      <button
                        className="btn-secondary"
                        style={{ padding: "6px 12px", fontSize: "0.8125rem" }}
                        onClick={() => handleSetActive(business.id)}
                      >
                        Set Active
                      </button>
                    )}
                    <button
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: "0.8125rem" }}
                      onClick={() => handleOpenEdit(business)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn-danger"
                      style={{ padding: "6px 12px", fontSize: "0.8125rem", backgroundColor: "rgba(239, 68, 68, 0.1)", color: "var(--danger-600)", border: "1px solid rgba(239, 68, 68, 0.2)" }}
                      onClick={() => setDeletingId(business.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {(view === "create" || view === "edit") && (
        <div className="settings-card">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px" }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ padding: "6px 10px", width: "auto" }}
              onClick={() => setView("list")}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12,19 5,12 12,5" />
              </svg>
            </button>
            <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "var(--slate-900)" }}>
              {view === "create" ? "Add new business profile" : `Edit profile: ${editingBusiness?.name}`}
            </h3>
          </div>

          <form onSubmit={handleSubmit} className="standard-form">
            <h4 style={{ fontSize: "0.875rem", fontWeight: "600", borderBottom: "1px solid var(--slate-200)", paddingBottom: "6px", color: "var(--slate-800)", marginBottom: "12px" }}>
              General Information
            </h4>

            <div style={{ display: "flex", gap: "16px", alignItems: "center", marginBottom: "20px" }}>
              <div style={{
                width: "80px",
                height: "80px",
                borderRadius: "8px",
                backgroundColor: "var(--brand-100)",
                color: "var(--brand-700)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.75rem",
                fontWeight: "700",
                position: "relative",
                overflow: "hidden",
                border: "2px dashed #30363d"
              }}>
                {formData.logo_url ? (
                  <img src={formData.logo_url} alt="Logo preview" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                ) : (
                  getInitials(formData.name)
                )}
                {logoUploading && (
                  <div className="avatar-uploading-overlay">
                    <div className="spinner white" />
                  </div>
                )}
              </div>
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleLogoUpload}
                  accept="image/*"
                  style={{ display: "none" }}
                />
                <button
                  type="button"
                  className="avatar-edit-badge-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={logoUploading}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: "4px" }}>
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17,8 12,3 7,8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Upload logo
                </button>
                <p style={{ fontSize: "0.75rem", color: "var(--slate-400)", marginTop: "4px" }}>
                  PNG, JPG, or GIF. Max size 5MB.
                </p>
              </div>
            </div>

            <div className="grid-2">
              <div className="settings-form-group">
                <label className="form-label" htmlFor="name">Business / Store Name *</label>
                <input
                  className={inputClass("name")}
                  type="text"
                  name="name"
                  id="name"
                  required
                  maxLength={255}
                  placeholder="E.g., Super Market Store"
                  value={formData.name}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.name && errors.name && <span className="field-error">{errors.name}</span>}
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="gst_number">GST Number</label>
                <input
                  className={inputClass("gst_number")}
                  type="text"
                  name="gst_number"
                  id="gst_number"
                  maxLength={30}
                  placeholder="E.g., 22AAAAA1111A1Z1"
                  value={formData.gst_number}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.gst_number && errors.gst_number && <span className="field-error">{errors.gst_number}</span>}
              </div>
            </div>

            <div className="grid-2">
              <div className="settings-form-group">
                <label className="form-label" htmlFor="phone">Phone Number</label>
                <input
                  className={inputClass("phone")}
                  type="tel"
                  name="phone"
                  id="phone"
                  maxLength={20}
                  placeholder="E.g., +91 9999999999"
                  value={formData.phone}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.phone && errors.phone && <span className="field-error">{errors.phone}</span>}
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="email">Business Email</label>
                <input
                  className={inputClass("email")}
                  type="email"
                  name="email"
                  id="email"
                  maxLength={255}
                  placeholder="E.g., info@store.com"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.email && errors.email && <span className="field-error">{errors.email}</span>}
              </div>
            </div>

            <h4 style={{ fontSize: "0.875rem", fontWeight: "600", borderBottom: "1px solid var(--slate-200)", paddingBottom: "6px", color: "var(--slate-800)", marginBottom: "12px", marginTop: "16px" }}>
              Address & Local Settings
            </h4>

            <div className="settings-form-group">
              <label className="form-label" htmlFor="address">Address</label>
              <input
                className={inputClass("address")}
                type="text"
                name="address"
                id="address"
                placeholder="Street address, shop number, etc."
                value={formData.address}
                onChange={handleChange}
                onBlur={handleBlur}
              />
              {touched.address && errors.address && <span className="field-error">{errors.address}</span>}
            </div>

            <div className="grid-3">
              <div className="settings-form-group">
                <label className="form-label" htmlFor="city">City</label>
                <input
                  className={inputClass("city")}
                  type="text"
                  name="city"
                  id="city"
                  maxLength={100}
                  placeholder="City"
                  value={formData.city}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.city && errors.city && <span className="field-error">{errors.city}</span>}
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="state">State</label>
                <input
                  className={inputClass("state")}
                  type="text"
                  name="state"
                  id="state"
                  maxLength={100}
                  placeholder="State"
                  value={formData.state}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.state && errors.state && <span className="field-error">{errors.state}</span>}
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="postal_code">Postal Code</label>
                <input
                  className={inputClass("postal_code")}
                  type="text"
                  name="postal_code"
                  id="postal_code"
                  maxLength={20}
                  placeholder="PIN / Zip Code"
                  value={formData.postal_code}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.postal_code && errors.postal_code && <span className="field-error">{errors.postal_code}</span>}
              </div>
            </div>

            <div className="grid-3">
              <div className="settings-form-group">
                <label className="form-label" htmlFor="invoice_prefix">Invoice Prefix</label>
                <input
                  className={inputClass("invoice_prefix")}
                  type="text"
                  name="invoice_prefix"
                  id="invoice_prefix"
                  maxLength={20}
                  placeholder="E.g., INV"
                  value={formData.invoice_prefix}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {touched.invoice_prefix && errors.invoice_prefix && <span className="field-error">{errors.invoice_prefix}</span>}
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="currency">Currency</label>
                <select
                  className={inputClass("currency", "form-select")}
                  name="currency"
                  id="currency"
                  value={formData.currency}
                  onChange={handleChange}
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
              <div className="settings-form-group">
                <label className="form-label" htmlFor="timezone">Timezone</label>
                <select
                  className={inputClass("timezone", "form-select")}
                  name="timezone"
                  id="timezone"
                  value={formData.timezone}
                  onChange={handleChange}
                >
                  <option value="Asia/Kolkata">Asia/Kolkata</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">America/New_York</option>
                  <option value="Europe/London">Europe/London</option>
                </select>
              </div>
            </div>

            <div className="flex-gap-2 mt-4" style={{ justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn-secondary"
                style={{ width: "auto" }}
                onClick={() => setView("list")}
                disabled={submitting || logoUploading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                style={{ width: "auto" }}
                disabled={submitting || logoUploading}
              >
                {submitting ? (
                  <span className="btn-loader">
                    <span className="spinner" />
                    Saving profile...
                  </span>
                ) : (
                  "Save business settings"
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default BusinessSettings;
