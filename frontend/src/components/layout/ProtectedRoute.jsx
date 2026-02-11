import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

// TODO: Remove DEV_MODE bypass when Week 2 auth is implemented
const DEV_MODE = true;

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading, isAuthenticated } = useAuth();

  if (DEV_MODE) return children;

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
