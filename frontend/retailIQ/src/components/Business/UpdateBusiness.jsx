import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { fetch_business, update_business } from "../../features/business/businessThunk";
import { validateField, validateForm, hasErrors, BUSINESS_RULES } from "../../utils/formValidation";

const UpdateBusiness = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const userId = useSelector((state) => state.auth.user?.id);
  const { businesses, selectedBusinessId, data: businessDetails, loading, error } = useSelector(
    (state) => state.business
  );
  const activeBusiness = businessDetails || businesses.find((b) => b.id === selectedBusinessId);
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
  useEffect(() => {
    if (userId && selectedBusinessId && !businessDetails) {
      dispatch(fetch_business(userId, selectedBusinessId));
    }
  }, [dispatch, userId, selectedBusinessId, businessDetails]);
  useEffect(() => {
    if (activeBusiness) {
      const timer = setTimeout(() => {
        setFormData({
          name: activeBusiness.name || "",
          gst_number: activeBusiness.gst_number || "",
          phone: activeBusiness.phone || "",
          email: activeBusiness.email || "",
          address: activeBusiness.address || "",
          city: activeBusiness.city || "",
          state: activeBusiness.state || "",
          country: activeBusiness.country || "India",
          postal_code: activeBusiness.postal_code || "",
          logo_url: activeBusiness.logo_url || "",
          invoice_prefix: activeBusiness.invoice_prefix || "INV",
          currency: activeBusiness.currency || "INR",
          timezone: activeBusiness.timezone || "Asia/Kolkata",
        });
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [activeBusiness]);
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
  const handleSubmit = async (e) => {
    e.preventDefault();
    const allTouched = {};
    Object.keys(BUSINESS_RULES).forEach((k) => (allTouched[k] = true));
    setTouched(allTouched);
    const formErrors = validateForm(formData, BUSINESS_RULES);
    setErrors(formErrors);
    if (hasErrors(formErrors)) return;
    if (!selectedBusinessId) return;
    await dispatch(update_business(formData, selectedBusinessId));
    navigate("/show");
  };
  const renderError = (fieldName) =>
    touched[fieldName] && errors[fieldName] ? (
      <span className="field-error">{errors[fieldName]}</span>
    ) : null;
  const inputClass = (fieldName, base = "form-input") =>
    `${base}${touched[fieldName] && errors[fieldName] ? " invalid" : ""}`;
  return (
    <div className="dashboard-page">
      <main className="dashboard-main">
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div className="dashboard-header">
            <h1 className="dashboard-greeting">Edit Business Profile</h1>
            <p className="dashboard-tagline">Update your store settings and corporate details.</p>
          </div>
          <div className="auth-card" style={{ maxWidth: "none" }}>
            {error && (
              <div className="auth-error">
                <span>{typeof error === "string" ? error : "Failed to update business profile"}</span>
              </div>
            )}
            <form onSubmit={handleSubmit} className="standard-form">
              <h3 style={{ borderBottom: "1px solid var(--slate-200)", paddingBottom: "8px", color: "var(--slate-800)" }}>
                Basic Information
              </h3>
              <div className="grid-2">
                <div className="form-group">
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
                  {renderError("name")}
                </div>
                <div className="form-group">
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
                  {renderError("gst_number")}
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
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
                  {renderError("phone")}
                </div>
                <div className="form-group">
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
                  {renderError("email")}
                </div>
              </div>
              <h3 style={{ borderBottom: "1px solid var(--slate-200)", paddingBottom: "8px", marginTop: "12px", color: "var(--slate-800)" }}>
                Address & Settings
              </h3>
              <div className="form-group">
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
                {renderError("address")}
              </div>
              <div className="grid-3">
                <div className="form-group">
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
                  {renderError("city")}
                </div>
                <div className="form-group">
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
                  {renderError("state")}
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="postal_code">Postal Code</label>
                  <input
                    className={inputClass("postal_code")}
                    type="text"
                    name="postal_code"
                    id="postal_code"
                    maxLength={20}
                    placeholder="PIN Code"
                    value={formData.postal_code}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  {renderError("postal_code")}
                </div>
              </div>
              <div className="grid-3">
                <div className="form-group">
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
                  {renderError("invoice_prefix")}
                </div>
                <div className="form-group">
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
                <div className="form-group">
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
              <div className="form-group">
                <label className="form-label" htmlFor="logo_url">Logo Image URL</label>
                <input
                  className={inputClass("logo_url")}
                  type="text"
                  name="logo_url"
                  id="logo_url"
                  placeholder="https://example.com/logo.png"
                  value={formData.logo_url}
                  onChange={handleChange}
                  onBlur={handleBlur}
                />
                {renderError("logo_url")}
              </div>
              <div className="flex-gap-2 mt-4" style={{ justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => navigate("/show")}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ width: "auto" }}
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};
export default UpdateBusiness;