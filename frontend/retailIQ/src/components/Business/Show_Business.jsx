import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { fetch_business, delete_business } from "../../features/business/businessThunk";

const Show_Business = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const userId = useSelector((state) => state.auth.user?.id);
  const { businesses, selectedBusinessId, data: businessDetails, loading, error } = useSelector(
    (state) => state.business
  );
  useEffect(() => {
    if (!userId || !selectedBusinessId) return;
    dispatch(fetch_business(userId, selectedBusinessId));
  }, [dispatch, userId, selectedBusinessId]);
  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this business profile? This will also delete all associated products and invoices, and cannot be undone.")) {
      await dispatch(delete_business(selectedBusinessId));
      navigate("/dashboard");
    }
  };
  const business = businessDetails || businesses.find(b => b.id === selectedBusinessId);
  return (
    <div className="dashboard-page">
      <main className="dashboard-main">
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div className="dashboard-header flex-between">
            <div>
              <h1 className="dashboard-greeting">Business Settings</h1>
              <p className="dashboard-tagline">Manage your store information, tax credentials, and system settings.</p>
            </div>
            {business && (
              <div className="flex-gap-2">
                <button
                  className="btn-secondary"
                  onClick={() => navigate("/business/edit")}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  Edit Profile
                </button>
                <button
                  className="btn-danger"
                  onClick={handleDelete}
                >
                  Delete Business
                </button>
              </div>
            )}
          </div>
          <div className="auth-card" style={{ maxWidth: "none" }}>
            {loading && !business ? (
              <div style={{ textAlign: "center", padding: "40px" }}>
                <span className="spinner" style={{ display: "inline-block" }} />
                <p style={{ marginTop: "12px", color: "var(--slate-500)" }}>Loading details...</p>
              </div>
            ) : !business ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--slate-500)" }}>
                No active business profile selected.
              </div>
            ) : (
              <div className="standard-form">
                {error && (
                  <div className="auth-error">
                    <span>{typeof error === "string" ? error : "An error occurred."}</span>
                  </div>
                )}
                <div style={{ display: "flex", gap: "24px", alignItems: "center", borderBottom: "1px solid var(--slate-200)", paddingBottom: "20px", marginBottom: "20px" }}>
                  {business.logo_url ? (
                    <img
                      src={business.logo_url}
                      alt="Logo"
                      style={{ width: "80px", height: "80px", borderRadius: "8px", objectFit: "contain", border: "1px solid var(--slate-200)" }}
                    />
                  ) : (
                    <div style={{ width: "80px", height: "80px", borderRadius: "8px", background: "var(--slate-100)", color: "var(--slate-500)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold", fontSize: "2rem", border: "1px solid var(--slate-200)" }}>
                      {business.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h2 style={{ fontSize: "1.5rem", color: "var(--slate-900)" }}>{business.name}</h2>
                    <p style={{ color: "var(--slate-500)", fontSize: "0.875rem" }}>
                      Created at: {new Date(business.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>GST Number</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.gst_number || "—"}</div>
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Phone Number</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.phone || "—"}</div>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Email Address</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.email || "—"}</div>
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Full Address</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>
                      {business.address ? (
                        <>
                          {business.address}
                          {business.city && `, ${business.city}`}
                          {business.state && `, ${business.state}`}
                          {business.postal_code && ` - ${business.postal_code}`}
                          {business.country && `, ${business.country}`}
                        </>
                      ) : "—"}
                    </div>
                  </div>
                </div>
                <h3 style={{ borderBottom: "1px solid var(--slate-200)", paddingBottom: "8px", marginTop: "16px", color: "var(--slate-800)" }}>
                  Regional & Invoicing Config
                </h3>
                <div className="grid-3">
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Invoice Prefix</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.invoice_prefix || "—"}</div>
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Currency</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.currency || "—"}</div>
                  </div>
                  <div className="form-group">
                    <label className="form-label" style={{ color: "var(--slate-500)" }}>Timezone</label>
                    <div style={{ fontSize: "1rem", fontWeight: "500" }}>{business.timezone || "—"}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
export default Show_Business;