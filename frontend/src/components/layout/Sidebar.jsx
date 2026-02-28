import { NavLink } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import {
  FileText,
  BarChart3,
  LayoutDashboard,
  Download,
} from "lucide-react";

const adminLinks = [
  { to: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/admin/documents", icon: FileText, label: "Documents" },
  { to: "/admin/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/admin/reports", icon: Download, label: "Reports" },
];

export default function Sidebar() {
  const { user } = useAuth();

  // Only admin uses the shared sidebar.
  // Customers have Chat's built-in sidebar; agents have AgentLayout.
  if (user?.role !== "admin") return null;

  return (
    <aside className="hidden w-56 shrink-0 border-r bg-muted/40 md:block">
      <nav className="flex flex-col gap-1 p-4">
        {adminLinks.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
