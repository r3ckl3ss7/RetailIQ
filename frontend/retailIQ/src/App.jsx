import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Dashboard from "./components/Dashboard";
import ProtectedRoute from "./routes/ProtectedRoutes";
import Business  from "./components/Business/Business";
import Show_Business from "./components/Business/Show_Business";
import UpdateBusiness from "./components/Business/UpdateBusiness";
import Products from "./components/Products/Products";
import Layout from "./components/Layout";
import Invoices from "./components/Invoice/Invoices";

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/business"
        element={
          <ProtectedRoute>
            <Layout>
              <Business />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/business/edit"
        element={
          <ProtectedRoute>
            <Layout>
              <UpdateBusiness />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/show"
        element={
          <ProtectedRoute>
            <Layout>
              <Show_Business/>
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/products"
        element={
          <ProtectedRoute>
            <Layout>
              <Products />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/invoices"
        element={
          <ProtectedRoute>
            <Layout>
              <Invoices />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;