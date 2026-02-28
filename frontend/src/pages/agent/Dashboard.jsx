import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getTickets } from "@/services/ticketApi";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Ticket, Clock, CheckCircle, ArrowRight } from "lucide-react";

const PRIORITY_VARIANT = {
  high: "destructive",
  medium: "default",
  low: "secondary",
};

const STATUS_VARIANT = {
  open: "destructive",
  in_progress: "default",
  resolved: "secondary",
  closed: "outline",
};

function formatStatus(s) {
  return s
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function AgentDashboard() {
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["tickets"],
    queryFn: () => getTickets({ limit: 100 }),
    refetchInterval: 10000,
  });

  const tickets = data?.items || [];
  const openCount = tickets.filter((t) => t.status === "open").length;
  const inProgressCount = tickets.filter((t) => t.status === "in_progress").length;
  const resolvedCount = tickets.filter((t) => t.status === "resolved").length;

  // Show most recent 5 open/in-progress tickets
  const recentTickets = tickets
    .filter((t) => t.status === "open" || t.status === "in_progress")
    .slice(0, 5);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Agent Dashboard</h1>
        <p className="text-muted-foreground">
          Manage escalated tickets and support requests
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Open Tickets</CardTitle>
            <Ticket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-12" /> : openCount}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-12" /> : inProgressCount}
            </div>
            <p className="text-xs text-muted-foreground">Being worked on</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? <Skeleton className="h-8 w-12" /> : resolvedCount}
            </div>
            <p className="text-xs text-muted-foreground">Tickets closed</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent tickets */}
      <Card className="mt-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Active Tickets</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/agent/tickets")}
          >
            View All
            <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : recentTickets.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No active tickets. Escalated conversations will appear here.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTickets.map((ticket) => (
                  <TableRow
                    key={ticket.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/agent/tickets/${ticket.id}`)}
                  >
                    <TableCell className="font-medium">#{ticket.id}</TableCell>
                    <TableCell>{ticket.customer_name || "Unknown"}</TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {ticket.conversation_title || ticket.reason || "Escalated conversation"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={PRIORITY_VARIANT[ticket.priority] || "secondary"}>
                        {ticket.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[ticket.status] || "secondary"}>
                        {formatStatus(ticket.status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
