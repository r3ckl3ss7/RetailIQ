import { configureStore } from "@reduxjs/toolkit";
import authReducer from "../features/auth/authSlice";
import businessReducer from "../features/business/businessSlice";
import productReducer from "../features/product/productSlice";
import invoiceReducer from "../features/invoice/invoiceSlice";
import chatReducer from "../features/chat/chatSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    business: businessReducer,
    products: productReducer,
    invoices: invoiceReducer,
    chat: chatReducer,
  },
});
export default store;

