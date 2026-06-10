import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Dashboard from "./components/Dashboard";
import ProtectedRoute from "./routes/ProtectedRoutes";
import Business  from "./components/Business/Business";
import Show_Business from "./components/Business/Show_Business";
import UpdateBusiness from "./components/Business/UpdateBusiness";
import Products from "./components/Products/Products";
const App = () => {
  return (
    <Routes>
      {}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      {}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route path="/business" element={
        <ProtectedRoute>
          <Business />
        </ProtectedRoute>
      } />
      <Route
        path="/business/edit"
        element={
          <ProtectedRoute>
            <UpdateBusiness />
          </ProtectedRoute>
        }
      />
      <Route path="/show" element={
        <ProtectedRoute>
          <Show_Business/>
        </ProtectedRoute>
      }>
      </Route>
      <Route
        path="/products"
        element={
          <ProtectedRoute>
            <Products />
          </ProtectedRoute>
        }
      />
      {}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
export default App;