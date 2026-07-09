import { createSlice } from "@reduxjs/toolkit";
import {
    fetchInvoiceMetadata,
    fetchInvoices,
    fetchInvoiceById,
    fetchCustomers,
    createInvoice,
    updateInvoice,
} from "./invoiceThunk";
const initialState = {
    data: [],
    selectedInvoice: null,
    metadata: null,
    customers: [],
    loading: false,
    error: null,
};
const invoiceSlice = createSlice({
    name: "invoices",
    initialState,
    reducers: {
        clearInvoices: (state) => {
            state.data = [];
        },
        clearSelectedInvoice: (state) => {
            state.selectedInvoice = null;
        },
        clearInvoiceError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchInvoiceMetadata.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchInvoiceMetadata.fulfilled, (state, action) => {
                state.loading = false;
                state.metadata = action.payload;
                state.error = null;
            })
            .addCase(fetchInvoiceMetadata.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(fetchInvoices.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchInvoices.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload && typeof action.payload === "object" && "items" in action.payload) {
                    state.data = action.payload.items || [];
                    state.total = action.payload.total || 0;
                } else {
                    state.data = action.payload || [];
                    state.total = (action.payload || []).length;
                }
                state.error = null;
            })
            .addCase(fetchInvoices.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(fetchInvoiceById.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchInvoiceById.fulfilled, (state, action) => {
                state.loading = false;
                state.selectedInvoice = action.payload;
                state.error = null;
            })
            .addCase(fetchInvoiceById.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(fetchCustomers.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchCustomers.fulfilled, (state, action) => {
                state.loading = false;
                state.customers = action.payload;
                state.error = null;
            })
            .addCase(fetchCustomers.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(createInvoice.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createInvoice.fulfilled, (state, action) => {
                state.loading = false;
                state.data.unshift(action.payload);
                state.selectedInvoice = action.payload;
                state.error = null;
            })
            .addCase(createInvoice.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            .addCase(updateInvoice.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateInvoice.fulfilled, (state, action) => {
                state.loading = false;
                const index = state.data.findIndex(
                    (invoice) => invoice.id === action.payload.id
                );
                if (index !== -1) {
                    state.data[index] = action.payload;
                }
                if (state.selectedInvoice?.id === action.payload.id) {
                    state.selectedInvoice = action.payload;
                }
                state.error = null;
            })
            .addCase(updateInvoice.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});
export const { clearInvoices, clearSelectedInvoice, clearInvoiceError } =
    invoiceSlice.actions;
export default invoiceSlice.reducer;