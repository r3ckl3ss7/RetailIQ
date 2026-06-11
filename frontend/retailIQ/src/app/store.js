import { configureStore } from "@reduxjs/toolkit";
import authReducer from "../features/auth/authSlice";
import businessReducer from "../features/business/businessSlice";
import productReducer from "../features/product/productSlice";
import invoiceReducer from "../features/invoice/invoiceSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    business: businessReducer,
    products: productReducer,
    invoices: invoiceReducer,
  },
});
export default store;
