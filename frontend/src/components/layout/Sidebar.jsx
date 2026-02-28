import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import { getTickets } from "@/services/ticketApi";
import { cn } from "@/lib/utils";
import {
  MessageSquare,
  FileText,
  BarChart3,
  Ticket,
  LayoutDashboard,
  Download,
} from "lucide-react";

const customerLinks = [
  { to: "/chat", icon: MessageSquare, label: "Chat" },
];

const agentLinks = [
  { to: "/agent", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/agent/tickets", icon: Ticket, label: "Tickets", badgeKey: "tickets" },
];

const adminLinks = [
  { to: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/admin/documents", icon: FileText, label: "Documents" },
  { to: "/admin/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/admin/reports", icon: Download, label: "Reports" },
];

export default function Sidebar() {
  const { user } = useAuth();

  // Customers only have one link (Chat) — the chat page has its own sidebar,
  // so we hide the app sidebar entirely to avoid a double-sidebar layout.
  if (user?.role === "customer") return null;

  const isAgent = user?.role === "agent";

  // Poll open ticket count for agent badge
  const { data: ticketData } = useQuery({
    queryKey: ["ticketsBadge"],
    queryFn: () => getTickets({ status: "open", limit: 1 }),
    enabled: isAgent,
    refetchInterval: 10000,
  });

  const openCount = ticketData?.total ?? 0;
  const badges = { tickets: openCount };

  const links =
    user?.role === "admin"
      ? adminLinks
      : isAgent
        ? agentLinks
        : customerLinks;

  return (
    <aside className="hidden w-56 shrink-0 border-r bg-muted/40 md:block">
      <nav className="flex flex-col gap-1 p-4">
        {links.map(({ to, icon: Icon, label, badgeKey }) => (
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
            <span className="flex-1">{label}</span>
            {badgeKey && badges[badgeKey] > 0 && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-[10px] font-bold text-white">
                {badges[badgeKey] > 99 ? "99+" : badges[badgeKey]}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
