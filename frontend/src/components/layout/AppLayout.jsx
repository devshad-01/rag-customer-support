import { Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  const { user } = useAuth();
  const { pathname } = useLocation();

  // Chat page uses a full-bleed layout (its own conversation sidebar)
  const isFullBleed = user?.role === "customer" && pathname.startsWith("/chat");

  // Full-bleed routes get no Navbar, no Sidebar, no padding
  if (isFullBleed) {
    return <Outlet />;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
