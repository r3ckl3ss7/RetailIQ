import { useEffect, useState, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import {
  fetchInvoices,
  fetchCustomers,
  createInvoice,
  createInvoiceOCR,
  updateInvoice,
} from "../../features/invoice/invoiceThunk";
import { fetchProducts } from "../../features/product/productThunk";
import { clearSelectedInvoice, clearInvoiceError } from "../../features/invoice/invoiceSlice";

const Invoices = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Redux Selectors
  const { selectedBusinessId, businesses } = useSelector((state) => state.business);
  const { data: invoices, customers, loading, error } = useSelector((state) => state.invoices);
  const { data: products } = useSelector((state) => state.products);
  const selectedBusiness = businesses.find((b) => b.id === selectedBusinessId);

  // Component States
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [viewingInvoice, setViewingInvoice] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState("");
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState("");

  // Invoice Form State
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [formData, setFormData] = useState({
    customerId: "",
    newCustomer: {
      name: "",
      phone_number: "",
      email: "",
    },
    status: "PENDING",
    notes: "",
    discount: "0",
    taxRate: "18", // GST default 18%
  });
  const [selectedItems, setSelectedItems] = useState([]); // Array of { product_id, quantity, product }
  const [currentItem, setCurrentItem] = useState({
    product_id: "",
    quantity: "1",
  });
  const [formError, setFormError] = useState("");

  // Fetch data on load/business shift
  useEffect(() => {
    if (selectedBusinessId) {
      dispatch(fetchInvoices(selectedBusinessId));
      dispatch(fetchCustomers(selectedBusinessId));
      dispatch(fetchProducts(selectedBusinessId));
    }
  }, [dispatch, selectedBusinessId]);

  // Clean errors when closing forms
  useEffect(() => {
    if (!showCreateForm) {
      setFormError("");
      setSelectedItems([]);
      setFormData({
        customerId: "",
        newCustomer: { name: "", phone_number: "", email: "" },
        status: "PENDING",
        notes: "",
        discount: "0",
        taxRate: "18",
      });
      setCurrentItem({ product_id: "", quantity: "1" });
    }
  }, [showCreateForm]);

  const formatCurrency = (value) => {
    const currencySymbol = selectedBusiness?.currency || "INR";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currencySymbol,
    }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleString("en-IN", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const renderNotes = (notes) => {
    if (!notes) return null;
    try {
      const parsed = JSON.parse(notes);
      if (parsed && typeof parsed === "object" && (parsed.ocr_confidence || parsed.ocr_text || parsed.unknown_items)) {
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" }}>
            {parsed.ocr_confidence && (
              <p style={{ fontSize: "0.8125rem", margin: 0, color: "var(--slate-600)" }}>
                AI OCR Confidence: <strong>{Math.round(parsed.ocr_confidence * 100)}%</strong>
              </p>
            )}
            {parsed.unknown_items && parsed.unknown_items.length > 0 && (
              <div style={{ marginTop: "4px" }}>
                <p style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--danger-600)", margin: "0 0 4px 0" }}>
                  Unresolved Scanned Items:
                </p>
                <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.8125rem", color: "var(--slate-500)" }}>
                  {parsed.unknown_items.map((item, i) => (
                    <li key={i}>
                      {item.name} (Qty: {item.quantity}, Price: {formatCurrency(item.amount)})
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {parsed.ocr_text && (
              <details style={{ marginTop: "6px" }}>
                <summary style={{ fontSize: "0.75rem", color: "var(--slate-400)", cursor: "pointer", outline: "none" }}>
                  Show raw extracted text
                </summary>
                <pre style={{ fontSize: "0.6875rem", background: "var(--slate-50)", padding: "8px", borderRadius: "4px", whiteSpace: "pre-wrap", overflowX: "auto", marginTop: "4px", maxHeight: "120px" }}>
                  {parsed.ocr_text}
                </pre>
              </details>
            )}
          </div>
        );
      }
    } catch (e) {
      // Not JSON, fallback
    }
    return (
      <p style={{ fontSize: "0.8125rem", color: "var(--slate-500)", marginTop: "4px", whiteSpace: "pre-line" }}>
        {notes}
      </p>
    );
  };

  // Calculations for Creation Form
  const subtotal = selectedItems.reduce((sum, item) => {
    return sum + (item.product?.selling_price || 0) * parseInt(item.quantity || 1);
  }, 0);

  const tax = subtotal * (parseFloat(formData.taxRate) / 100);
  const discountVal = parseFloat(formData.discount) || 0;
  const total = subtotal + tax - discountVal;

  // Manual Invoice Items manipulation
  const handleAddItem = () => {
    if (!currentItem.product_id) {
      setFormError("Please select a product first.");
      return;
    }
    const quantity = parseInt(currentItem.quantity);
    if (isNaN(quantity) || quantity <= 0) {
      setFormError("Quantity must be at least 1.");
      return;
    }

    const matchedProduct = products.find((p) => p.id === parseInt(currentItem.product_id));
    if (!matchedProduct) return;

    // Check if item already added
    const existingIndex = selectedItems.findIndex(
      (item) => item.product_id === matchedProduct.id
    );

    if (existingIndex !== -1) {
      const updated = [...selectedItems];
      updated[existingIndex].quantity = (
        parseInt(updated[existingIndex].quantity) + quantity
      ).toString();
      setSelectedItems(updated);
    } else {
      setSelectedItems([
        ...selectedItems,
        {
          product_id: matchedProduct.id,
          quantity: currentItem.quantity,
          product: matchedProduct,
        },
      ]);
    }

    // Reset current item selections
    setCurrentItem({ product_id: "", quantity: "1" });
    setFormError("");
  };

  const handleRemoveItem = (index) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  // Invoice Submissions
  const handleSubmitInvoice = async (e) => {
    e.preventDefault();
    setFormError("");

    if (!selectedBusinessId) return;

    if (selectedItems.length === 0) {
      setFormError("Please add at least one product line item.");
      return;
    }

    if (isNewCustomer) {
      if (!formData.newCustomer.name || !formData.newCustomer.phone_number) {
        setFormError("Customer Name and Phone Number are required for new customers.");
        return;
      }
    } else {
      if (!formData.customerId) {
        setFormError("Please select an existing customer or toggle New Customer.");
        return;
      }
    }

    const payload = {
      business_id: parseInt(selectedBusinessId),
      status: formData.status,
      notes: formData.notes || null,
      subtotal: parseFloat(subtotal.toFixed(2)),
      tax: parseFloat(tax.toFixed(2)),
      discount: parseFloat(discountVal.toFixed(2)),
      total: parseFloat(total.toFixed(2)),
      items: selectedItems.map((item) => ({
        product_id: item.product_id,
        quantity: parseInt(item.quantity),
      })),
    };

    if (isNewCustomer) {
      payload.customer = {
        name: formData.newCustomer.name,
        phone_number: formData.newCustomer.phone_number,
        email: formData.newCustomer.email || null,
      };
    } else {
      payload.customer_id = parseInt(formData.customerId);
    }

    const result = await dispatch(createInvoice(payload));
    if (!result.error) {
      setShowCreateForm(false);
      dispatch(fetchInvoices(selectedBusinessId));
      dispatch(fetchCustomers(selectedBusinessId));
    } else {
      const errMessage = result.payload?.detail || result.payload?.error || (typeof result.payload === "string" ? result.payload : "Failed to create invoice.");
      setFormError(errMessage);
    }
  };

  // OCR Upload Actions
  const handleOcrClick = () => {
    fileInputRef.current.click();
  };

  const handleOcrFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate type
    if (!file.type.startsWith("image/")) {
      setOcrError("Please upload an image file (PNG, JPG, JPEG).");
      return;
    }

    setOcrLoading(true);
    setOcrError("");

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async () => {
      try {
        const rawBase64 = reader.result.split(",")[1];
        const result = await dispatch(
          createInvoiceOCR({
            business_id: parseInt(selectedBusinessId),
            image_base64: rawBase64,
            deduct_from_stock: true,
          })
        );

        if (!result.error) {
          dispatch(fetchInvoices(selectedBusinessId));
          // Open details of extracted invoice
          setViewingInvoice(result.payload);
        } else {
          setOcrError(
            typeof result.payload === "string"
              ? result.payload
              : "Failed to read receipt. Make sure pricing text is readable."
          );
        }
      } catch (err) {
        setOcrError("Failed to convert image. Please try another file.");
      } finally {
        setOcrLoading(false);
        // Clear input element
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    };
  };

  const handleUpdateStatus = async (newStatus) => {
    if (!viewingInvoice) return;
    setStatusLoading(true);
    setStatusError("");
    try {
      const result = await dispatch(
        updateInvoice({
          invoiceId: viewingInvoice.id,
          data: { status: newStatus },
        })
      );
      if (!result.error) {
        setViewingInvoice(result.payload);
        if (selectedBusinessId) {
          dispatch(fetchInvoices(selectedBusinessId));
        }
      } else {
        const errMessage =
          result.payload?.detail ||
          result.payload?.error ||
          (typeof result.payload === "string" ? result.payload : "Failed to update status.");
        setStatusError(errMessage);
      }
    } catch (err) {
      setStatusError("An unexpected error occurred.");
    } finally {
      setStatusLoading(false);
    }
  };

  // Status Badge Helper
  const getStatusBadge = (status) => {
    const s = status ? status.toUpperCase() : "PENDING";
    if (s === "PAID") return <span className="badge badge-success">Paid</span>;
    if (s === "PENDING") return <span className="badge badge-warning">Pending</span>;
    if (s === "DRAFT") return <span className="badge badge-neutral">Draft</span>;
    if (s === "CANCELLED" || s === "REFUNDED") return <span className="badge badge-danger">{status}</span>;
    return <span className="badge badge-neutral">{status}</span>;
  };

  // Print trigger
  const handlePrint = () => {
    window.print();
  };

  // Search filtering
  const filteredInvoices = invoices.filter((inv) => {
    const customerName = inv.customer?.name?.toLowerCase() || "";
    const invId = `inv-${inv.id}`;
    return (
      customerName.includes(searchQuery.toLowerCase()) ||
      invId.includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="dashboard-page">
      <main className="dashboard-main">
        {!selectedBusinessId ? (
          <div className="empty-state-card">
            <h2 className="empty-state-title">No Active Business Selected</h2>
            <p className="empty-state-description">
              Please create or select a business to manage your invoices.
            </p>
            <button className="btn-primary" style={{ width: "auto" }} onClick={() => navigate("/business")}>
              Create Business
            </button>
          </div>
        ) : (
          <>
            {/* Header Area */}
            <div className="dashboard-header flex-between flex-wrap gap-4">
              <div>
                <h1 className="dashboard-greeting">Invoices</h1>
                <p className="dashboard-tagline">
                  Generate manual bills, track billing status, and upload receipt scans for <strong>{selectedBusiness?.name}</strong>.
                </p>
              </div>
              {!showCreateForm && !viewingInvoice && (
                <div className="flex-gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: "none" }}
                    accept="image/*"
                    onChange={handleOcrFileChange}
                  />
                  <button
                    className="btn-secondary"
                    onClick={handleOcrClick}
                    disabled={ocrLoading}
                    style={{ borderStyle: "dashed" }}
                  >
                    {ocrLoading ? (
                      <>
                        <span className="spinner" style={{ width: "14px", height: "14px", marginRight: "4px" }} />
                        Scanning...
                      </>
                    ) : (
                      <>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: "4px" }}>
                          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                          <circle cx="12" cy="13" r="4" />
                        </svg>
                        OCR Scan Receipt
                      </>
                    )}
                  </button>
                  <button className="btn-primary" style={{ width: "auto" }} onClick={() => setShowCreateForm(true)}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: "4px" }}>
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    New Invoice
                  </button>
                </div>
              )}
            </div>

            {/* Error alerts */}
            {ocrError && (
              <div className="auth-error mb-4">
                <span>{ocrError}</span>
              </div>
            )}
            {error && (
              <div className="auth-error mb-4">
                <span>{typeof error === "string" ? error : "Something went wrong fetching invoices."}</span>
              </div>
            )}

            {/* Manual Creation Form */}
            {showCreateForm && (
              <div className="auth-card mb-6" style={{ maxWidth: "none" }}>
                <h3 className="mb-4" style={{ borderBottom: "1px solid var(--slate-200)", paddingBottom: "8px", color: "var(--slate-800)" }}>
                  Create Customer Invoice
                </h3>
                {formError && (
                  <div className="auth-error mb-4">
                    <span>{formError}</span>
                  </div>
                )}
                <form onSubmit={handleSubmitInvoice} className="standard-form">
                  <div className="grid-2">
                    {/* Customer Selection block */}
                    <div className="form-group" style={{ borderRight: "1px solid var(--slate-100)", paddingRight: "16px" }}>
                      <div className="flex-between mb-2">
                        <label className="form-label" style={{ marginBottom: 0 }}>Customer Info *</label>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                          onClick={() => setIsNewCustomer(!isNewCustomer)}
                        >
                          {isNewCustomer ? "Select Existing" : "+ Add New Customer"}
                        </button>
                      </div>

                      {isNewCustomer ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                          <input
                            className="form-input"
                            type="text"
                            placeholder="Full Name *"
                            required
                            value={formData.newCustomer.name}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                newCustomer: { ...formData.newCustomer, name: e.target.value },
                              })
                            }
                          />
                          <input
                            className="form-input"
                            type="tel"
                            placeholder="Phone Number *"
                            required
                            value={formData.newCustomer.phone_number}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                newCustomer: {
                                  ...formData.newCustomer,
                                  phone_number: e.target.value,
                                },
                              })
                            }
                          />
                          <input
                            className="form-input"
                            type="email"
                            placeholder="Email Address"
                            value={formData.newCustomer.email}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                newCustomer: { ...formData.newCustomer, email: e.target.value },
                              })
                            }
                          />
                        </div>
                      ) : (
                        <select
                          className="form-select"
                          value={formData.customerId}
                          onChange={(e) => setFormData({ ...formData, customerId: e.target.value })}
                          required
                        >
                          <option value="">-- Select Customer --</option>
                          {customers.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name} ({c.phone_number})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Meta options & notes */}
                    <div className="form-group">
                      <label className="form-label">Invoice Details</label>
                      <div className="grid-2 mb-2" style={{ gap: "10px" }}>
                        <div>
                          <label className="field-hint">Billing Status</label>
                          <select
                            className="form-select"
                            value={formData.status}
                            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                          >
                            <option value="PENDING">Pending</option>
                            <option value="DRAFT">Draft</option>
                            <option value="PAID">Paid</option>
                          </select>
                        </div>
                        <div>
                          <label className="field-hint">GST Rate (%)</label>
                          <select
                            className="form-select"
                            value={formData.taxRate}
                            onChange={(e) => setFormData({ ...formData, taxRate: e.target.value })}
                          >
                            <option value="0">0%</option>
                            <option value="5">5%</option>
                            <option value="12">12%</option>
                            <option value="18">18%</option>
                            <option value="28">28%</option>
                          </select>
                        </div>
                      </div>
                      <textarea
                        className="form-textarea"
                        placeholder="Additional billing notes or terms..."
                        style={{ minHeight: "68px", resize: "none" }}
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      />
                    </div>
                  </div>

                  {/* Add Product Items Block */}
                  <div style={{ borderTop: "1px solid var(--slate-100)", paddingTop: "16px", marginTop: "8px" }}>
                    <h4 className="mb-4" style={{ color: "var(--slate-800)", fontWeight: 600 }}>Line Items</h4>
                    <div className="flex-gap-2 mb-4 flex-wrap">
                      <select
                        className="form-select"
                        style={{ flex: 1, minWidth: "200px" }}
                        value={currentItem.product_id}
                        onChange={(e) =>
                          setCurrentItem({ ...currentItem, product_id: e.target.value })
                        }
                      >
                        <option value="">-- Add Product --</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} ({formatCurrency(p.selling_price)} - Stock: {p.stock})
                          </option>
                        ))}
                      </select>
                      <input
                        className="form-input"
                        type="number"
                        min="1"
                        placeholder="Qty"
                        style={{ width: "90px" }}
                        value={currentItem.quantity}
                        onChange={(e) =>
                          setCurrentItem({ ...currentItem, quantity: e.target.value })
                        }
                      />
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{ width: "auto" }}
                        onClick={handleAddItem}
                      >
                        Add Item
                      </button>
                    </div>

                    {/* Added Items table */}
                    {selectedItems.length > 0 && (
                      <div className="retail-table-container mb-4">
                        <table className="retail-table">
                          <thead>
                            <tr>
                              <th>Product</th>
                              <th style={{ textAlign: "right" }}>Price</th>
                              <th style={{ textAlign: "center" }}>Qty</th>
                              <th style={{ textAlign: "right" }}>Total</th>
                              <th style={{ textAlign: "center" }}>Remove</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedItems.map((item, idx) => (
                              <tr key={idx}>
                                <td>{item.product?.name}</td>
                                <td style={{ textAlign: "right" }}>
                                  {formatCurrency(item.product?.selling_price)}
                                </td>
                                <td style={{ textAlign: "center" }}>{item.quantity}</td>
                                <td style={{ textAlign: "right", fontWeight: "600" }}>
                                  {formatCurrency(item.product?.selling_price * parseInt(item.quantity))}
                                </td>
                                <td style={{ textAlign: "center" }}>
                                  <button
                                    type="button"
                                    onClick={() => handleRemoveItem(idx)}
                                    style={{
                                      background: "none",
                                      border: "none",
                                      color: "var(--danger-500)",
                                      cursor: "pointer",
                                    }}
                                  >
                                    ✕
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Financial calculation block */}
                  <div
                    style={{
                      borderTop: "1px solid var(--slate-100)",
                      paddingTop: "16px",
                      display: "flex",
                      justifyContent: "flex-end",
                    }}
                  >
                    <div style={{ width: "320px", display: "flex", flexDirection: "column", gap: "10px" }}>
                      <div className="flex-between">
                        <span style={{ color: "var(--slate-500)", fontSize: "0.875rem" }}>Subtotal:</span>
                        <span style={{ fontWeight: 600 }}>{formatCurrency(subtotal)}</span>
                      </div>
                      <div className="flex-between">
                        <span style={{ color: "var(--slate-500)", fontSize: "0.875rem" }}>
                          Tax ({formData.taxRate}%):
                        </span>
                        <span style={{ fontWeight: 600 }}>{formatCurrency(tax)}</span>
                      </div>
                      <div className="flex-between" style={{ alignItems: "center" }}>
                        <span style={{ color: "var(--slate-500)", fontSize: "0.875rem" }}>Discount Amount:</span>
                        <input
                          className="form-input"
                          type="number"
                          min="0"
                          step="0.01"
                          style={{ width: "120px", padding: "4px 8px", textAlign: "right" }}
                          value={formData.discount}
                          onChange={(e) => setFormData({ ...formData, discount: e.target.value })}
                        />
                      </div>
                      <div
                        className="flex-between"
                        style={{ borderTop: "1px dashed var(--slate-200)", paddingTop: "10px", marginTop: "4px" }}
                      >
                        <span style={{ fontWeight: "700", color: "var(--slate-800)" }}>Total Amount:</span>
                        <span style={{ fontWeight: "800", color: "var(--brand-500)", fontSize: "1.125rem" }}>
                          {formatCurrency(total)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action triggers */}
                  <div className="flex-gap-2 mt-4" style={{ justifyContent: "flex-end" }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setShowCreateForm(false)}
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
                      {loading ? "Creating..." : "Save Invoice"}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Receipt detail view */}
            {viewingInvoice && (
              <div className="auth-card mb-6" style={{ maxWidth: "800px", margin: "0 auto", padding: "40px" }} id="printable-invoice">
                {statusError && (
                  <div className="auth-error mb-4 no-print">
                    <span>{statusError}</span>
                  </div>
                )}
                {/* Print styling injection */}
                <style>{`
                  @media print {
                    body * {
                      visibility: hidden;
                    }
                    #printable-invoice, #printable-invoice * {
                      visibility: visible;
                    }
                    #printable-invoice {
                      position: absolute;
                      left: 0;
                      top: 0;
                      width: 100%;
                      border: none !important;
                      box-shadow: none !important;
                      padding: 0 !important;
                      margin: 0 !important;
                      background: white !important;
                      color: black !important;
                    }
                    .no-print {
                      display: none !important;
                    }
                  }
                `}</style>

                {/* Printable Invoice Header */}
                <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "2px solid var(--slate-100)", paddingBottom: "24px", marginBottom: "24px" }}>
                  <div>
                    <h2 style={{ fontSize: "1.75rem", fontWeight: "800", color: "var(--slate-800)", marginBottom: "4px" }}>
                      {selectedBusiness?.name}
                    </h2>
                    <p style={{ fontSize: "0.8125rem", color: "var(--slate-400)" }}>
                      {selectedBusiness?.address && `${selectedBusiness.address}, `}
                      {selectedBusiness?.city && `${selectedBusiness.city}, `}
                      {selectedBusiness?.state && `${selectedBusiness.state}`}
                    </p>
                    {selectedBusiness?.gst_number && (
                      <p style={{ fontSize: "0.8125rem", color: "var(--slate-500)", marginTop: "4px" }}>
                        GSTIN: <strong>{selectedBusiness.gst_number}</strong>
                      </p>
                    )}
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "var(--slate-400)", letterSpacing: "0.05em" }}>
                      Tax Invoice
                    </span>
                    <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "4px 0" }}>
                      #{selectedBusiness?.invoice_prefix || "INV"}-{viewingInvoice.id}
                    </h3>
                    <div>{getStatusBadge(viewingInvoice.status)}</div>
                  </div>
                </div>

                {/* Billing details block */}
                <div className="grid-2 mb-6" style={{ gap: "24px" }}>
                  <div>
                    <span className="form-label" style={{ color: "var(--slate-400)", fontSize: "0.75rem", textTransform: "uppercase" }}>
                      Bill To:
                    </span>
                    <h4 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--slate-800)", margin: "4px 0 2px 0" }}>
                      {viewingInvoice.customer?.name || "Cash Customer"}
                    </h4>
                    <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                      Phone: {viewingInvoice.customer?.phone_number || "—"}
                    </p>
                    <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                      Email: {viewingInvoice.customer?.email || "—"}
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span className="form-label" style={{ color: "var(--slate-400)", fontSize: "0.75rem", textTransform: "uppercase" }}>
                      Details:
                    </span>
                    <p style={{ fontSize: "0.875rem", color: "var(--slate-500)", marginTop: "4px" }}>
                      Date: <strong>{formatDate(viewingInvoice.created_at)}</strong>
                    </p>
                    <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                      Source: <span className="badge badge-neutral" style={{ fontSize: "0.6875rem", padding: "2px 6px" }}>{viewingInvoice.source}</span>
                    </p>
                  </div>
                </div>

                {/* Items details table */}
                <div className="retail-table-container mb-6" style={{ border: "1px solid var(--slate-100)" }}>
                  <table className="retail-table">
                    <thead>
                      <tr>
                        <th>Product / Item</th>
                        <th style={{ textAlign: "right" }}>Unit Price</th>
                        <th style={{ textAlign: "center" }}>Qty</th>
                        <th style={{ textAlign: "right" }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {viewingInvoice.items?.map((item, index) => (
                        <tr key={index}>
                          <td style={{ fontWeight: 600 }}>{item.product?.name || "Product"}</td>
                          <td style={{ textAlign: "right" }}>
                            {formatCurrency(item.product?.selling_price || 0)}
                          </td>
                          <td style={{ textAlign: "center" }}>{item.quantity}</td>
                          <td style={{ textAlign: "right", fontWeight: 600 }}>
                            {formatCurrency((item.product?.selling_price || 0) * item.quantity)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Printable Invoice Footer details */}
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "24px" }}>
                  <div style={{ flex: 1, minWidth: "200px" }}>
                    {viewingInvoice.notes && (
                      <>
                        <span className="form-label" style={{ color: "var(--slate-400)", fontSize: "0.75rem", textTransform: "uppercase" }}>
                          Notes:
                        </span>
                        {renderNotes(viewingInvoice.notes)}
                      </>
                    )}
                  </div>
                  <div style={{ width: "280px", display: "flex", flexDirection: "column", gap: "10px" }}>
                    <div className="flex-between">
                      <span style={{ color: "var(--slate-400)", fontSize: "0.875rem" }}>Subtotal:</span>
                      <span style={{ fontWeight: 600 }}>{formatCurrency(viewingInvoice.subtotal)}</span>
                    </div>
                    <div className="flex-between">
                      <span style={{ color: "var(--slate-400)", fontSize: "0.875rem" }}>Tax:</span>
                      <span style={{ fontWeight: 600 }}>{formatCurrency(viewingInvoice.tax)}</span>
                    </div>
                    <div className="flex-between">
                      <span style={{ color: "var(--slate-400)", fontSize: "0.875rem" }}>Discount:</span>
                      <span style={{ fontWeight: 600 }}>-{formatCurrency(viewingInvoice.discount)}</span>
                    </div>
                    <div className="flex-between" style={{ borderTop: "2px solid var(--slate-100)", paddingTop: "12px", marginTop: "4px" }}>
                      <span style={{ fontWeight: "700", color: "var(--slate-800)" }}>Total:</span>
                      <span style={{ fontWeight: "800", color: "var(--brand-500)", fontSize: "1.25rem" }}>
                        {formatCurrency(viewingInvoice.total)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Print control actions */}
                <div className="flex-gap-2 mt-6 no-print" style={{ justifyContent: "flex-end", borderTop: "1px solid var(--slate-100)", paddingTop: "16px" }}>
                  {(viewingInvoice.status === "PENDING" || viewingInvoice.status === "DRAFT") && (
                    <>
                      <button
                        className="btn-primary"
                        style={{ width: "auto" }}
                        onClick={() => handleUpdateStatus("PAID")}
                        disabled={statusLoading}
                      >
                        {statusLoading ? "Updating..." : "Mark as Paid"}
                      </button>
                      <button
                        className="btn-danger"
                        onClick={() => handleUpdateStatus("CANCELLED")}
                        disabled={statusLoading}
                      >
                        {statusLoading ? "Updating..." : "Cancel Invoice"}
                      </button>
                    </>
                  )}
                  {viewingInvoice.status === "PAID" && (
                    <>
                      <button
                        className="btn-danger"
                        onClick={() => handleUpdateStatus("REFUNDED")}
                        disabled={statusLoading}
                      >
                        {statusLoading ? "Updating..." : "Refund Invoice"}
                      </button>
                      <button
                        className="btn-danger"
                        onClick={() => handleUpdateStatus("CANCELLED")}
                        disabled={statusLoading}
                      >
                        {statusLoading ? "Updating..." : "Cancel Invoice"}
                      </button>
                    </>
                  )}
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setViewingInvoice(null);
                      setStatusError("");
                    }}
                    disabled={statusLoading}
                  >
                    Close Invoice
                  </button>
                  <button
                    className="btn-primary"
                    style={{ width: "auto" }}
                    onClick={handlePrint}
                    disabled={statusLoading}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginRight: "4px" }}>
                      <polyline points="6 9 6 2 18 2 18 9" />
                      <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                      <rect x="6" y="14" width="12" height="8" />
                    </svg>
                    Print / Print PDF
                  </button>
                </div>
              </div>
            )}

            {/* List Grid View */}
            {!showCreateForm && !viewingInvoice && (
              <>
                {/* Search query field */}
                <div style={{ display: "flex", gap: "16px", marginBottom: "20px" }}>
                  <div className="input-wrapper" style={{ flex: 1 }}>
                    <svg
                      className="input-icon"
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <input
                      className="form-input"
                      type="text"
                      placeholder="Search invoices by customer name or invoice number (e.g. inv-3)..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>

                {/* Invoices table grid */}
                <div className="retail-table-container">
                  {loading && invoices.length === 0 ? (
                    <div style={{ textAlign: "center", padding: "40px" }}>
                      <span className="spinner" style={{ display: "inline-block" }} />
                      <p style={{ marginTop: "12px", color: "var(--slate-500)" }}>Loading invoices...</p>
                    </div>
                  ) : filteredInvoices.length === 0 ? (
                    <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--slate-500)" }}>
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--slate-300)" strokeWidth="1.5" style={{ marginBottom: "12px" }}>
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                      </svg>
                      <h3>No Invoices Found</h3>
                      <p style={{ fontSize: "0.875rem" }}>
                        {searchQuery ? "Try refining your search terms." : "Create your first customer invoice manually or scan a billing receipt."}
                      </p>
                    </div>
                  ) : (
                    <table className="retail-table">
                      <thead>
                        <tr>
                          <th>Invoice ID</th>
                          <th>Customer</th>
                          <th>Date</th>
                          <th>Source</th>
                          <th style={{ textAlign: "right" }}>Total Amount</th>
                          <th style={{ textAlign: "center" }}>Status</th>
                          <th style={{ textAlign: "center" }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredInvoices.map((invoice) => (
                          <tr key={invoice.id}>
                            <td style={{ fontFamily: "monospace", fontWeight: "600", fontSize: "0.8125rem" }}>
                              #{selectedBusiness?.invoice_prefix || "INV"}-{invoice.id}
                            </td>
                            <td style={{ fontWeight: "600", color: "var(--slate-900)" }}>
                              {invoice.customer?.name || "Cash Customer"}
                            </td>
                            <td style={{ color: "var(--slate-500)", fontSize: "0.8125rem" }}>
                              {formatDate(invoice.created_at)}
                            </td>
                            <td>
                              <span className="badge badge-neutral" style={{ fontSize: "0.6875rem", padding: "2px 6px" }}>
                                {invoice.source}
                              </span>
                            </td>
                            <td style={{ textAlign: "right", fontWeight: "700", color: "var(--slate-900)" }}>
                              {formatCurrency(invoice.total)}
                            </td>
                            <td style={{ textAlign: "center" }}>
                              {getStatusBadge(invoice.status)}
                            </td>
                            <td style={{ textAlign: "center" }}>
                              <button
                                className="btn-secondary"
                                style={{ padding: "6px 10px", fontSize: "0.75rem" }}
                                onClick={() => {
                                  setViewingInvoice(invoice);
                                  setStatusError("");
                                }}
                              >
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default Invoices;
