import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import AppLayout from "@/components/layout/AppLayout";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import Landing from "@/pages/Landing";
import Chat from "@/pages/customer/Chat";
import AgentDashboard from "@/pages/agent/Dashboard";
import TicketDetail from "@/pages/agent/TicketDetail";
import TicketView from "@/pages/agent/TicketView";
import AdminDashboard from "@/pages/admin/Dashboard";
import Documents from "@/pages/admin/Documents";
import Analytics from "@/pages/admin/Analytics";
import Reports from "@/pages/admin/Reports";

function RoleRedirect() {
  const { loading } = useAuth();

  if (loading) return null;
  // Always show Landing — it handles logged-in vs logged-out state internally
  return <Landing />;
}

export default function App() {
  return (
    <Routes>
      {/* Public — Landing page handles both sign-in & register via tabs */}
      <Route path="/login" element={<Landing />} />
      <Route path="/register" element={<Landing />} />

      {/* Protected routes with layout */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* Customer */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute allowedRoles={["customer"]}>
              <Chat />
            </ProtectedRoute>
          }
        />

        {/* Agent */}
        <Route
          path="/agent"
          element={
            <ProtectedRoute allowedRoles={["agent"]}>
              <AgentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/agent/tickets"
          element={
            <ProtectedRoute allowedRoles={["agent"]}>
              <TicketDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/agent/tickets/:ticketId"
          element={
            <ProtectedRoute allowedRoles={["agent"]}>
              <TicketView />
            </ProtectedRoute>
          }
        />

        {/* Admin */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/documents"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <Documents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/reports"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <Reports />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Root redirect based on role */}
      <Route path="/" element={<RoleRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
