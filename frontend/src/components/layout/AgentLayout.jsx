import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { getTickets } from "@/services/ticketApi";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { SupportIQIcon } from "@/components/SupportIQLogo";
import {
  LayoutDashboard,
  Ticket,
  ChevronsLeft,
  PanelLeft,
  Moon,
  Sun,
  LogOut,
  User,
} from "lucide-react";

const agentLinks = [
  { to: "/agent", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/agent/tickets", icon: Ticket, label: "Tickets", badgeKey: "tickets" },
];

export default function AgentLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Poll open ticket count for badge
  const { data: ticketData } = useQuery({
    queryKey: ["ticketsBadge"],
    queryFn: () => getTickets({ status: "open", limit: 1 }),
    refetchInterval: 10000,
  });

  const openCount = ticketData?.total ?? 0;
  const badges = { tickets: openCount };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="relative flex h-screen bg-background p-3 gap-3">
      {/* Sidebar open button (visible when collapsed) */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute left-5 top-5 z-20 flex h-8 w-8 items-center justify-center rounded-lg border bg-background shadow-sm transition hover:bg-muted"
          title="Show sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "shrink-0 flex flex-col rounded-2xl bg-muted/40 border transition-all duration-200",
          sidebarOpen ? "w-56" : "w-0 overflow-hidden border-0 p-0"
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-2 px-3 pt-3 pb-2">
          <SupportIQIcon className="h-7 w-7 shrink-0" />
          <span className="text-sm font-semibold tracking-tight flex-1">
            SupportIQ
          </span>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setSidebarOpen(false)}
            title="Close sidebar"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
        </div>

        <Separator />

        {/* Navigation links */}
        <nav className="flex flex-col gap-0.5 p-2 flex-1">
          {agentLinks.map(({ to, icon: Icon, label, badgeKey }) => (
            <NavLink
              key={to}
              to={to}
              end
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{label}</span>
              {badgeKey && badges[badgeKey] > 0 && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white">
                  {badges[badgeKey] > 99 ? "99+" : badges[badgeKey]}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-800 dark:bg-neutral-600">
              <User className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium leading-tight">
                {user?.name}
              </p>
              <p className="truncate text-[11px] text-muted-foreground leading-tight">
                {user?.email}
              </p>
            </div>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground"
              onClick={toggleTheme}
              title={theme === "dark" ? "Light mode" : "Dark mode"}
            >
              {theme === "dark" ? (
                <Sun className="h-3.5 w-3.5" />
              ) : (
                <Moon className="h-3.5 w-3.5" />
              )}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={handleLogout}
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto rounded-2xl border bg-background">
        <Outlet />
      </main>
    </div>
  );
}
