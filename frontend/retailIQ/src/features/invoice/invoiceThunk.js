import { createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../services/api";
export const fetchInvoiceMetadata = createAsyncThunk(
    "invoices/fetchInvoiceMetadata",
    async (businessId, { rejectWithValue }) => {
        try {
            const response = await api.get("/invoice/", {
                params: { business_id: businessId },
            });
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
);
export const fetchInvoices = createAsyncThunk(
    "invoices/fetchInvoices",
    async (arg, { rejectWithValue }) => {
        try {
            let params = {};
            if (typeof arg === "object" && arg !== null) {
                params = {
                    business_id: arg.businessId,
                    ...(arg.page !== undefined && { page: arg.page }),
                    ...(arg.limit !== undefined && { limit: arg.limit }),
                };
            } else {
                params = { business_id: arg };
            }
            const response = await api.get("/invoice/list", { params });
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
);
export const fetchInvoiceById = createAsyncThunk(
    "invoices/fetchInvoiceById",
    async (invoiceId, { rejectWithValue }) => {
        try {
            const response = await api.get(`/invoice/${invoiceId}`);
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
);
export const fetchCustomers = createAsyncThunk(
    "invoices/fetchCustomers",
    async (businessId, { rejectWithValue }) => {
        try {
            const response = await api.get("/invoice/customers", {
                params: { business_id: businessId },
            });
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
)
export const createInvoice = createAsyncThunk(
    "invoices/createInvoice",
    async (data, { rejectWithValue }) => {
        try {
            const response = await api.post("/invoice/", data);
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
);
export const updateInvoice = createAsyncThunk(
    "invoices/updateInvoice",
    async ({ invoiceId, data }, { rejectWithValue }) => {
        try {
            const response = await api.patch(`/invoice/${invoiceId}`, data);
            return response.data;
        } catch (err) {
            return rejectWithValue(err.response?.data || { error: err.message });
        }
    }
);
