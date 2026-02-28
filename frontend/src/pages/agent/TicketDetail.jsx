import { useState } from "react";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowRight, Inbox } from "lucide-react";

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

function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TicketDetail() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("all");

  const { data, isLoading } = useQuery({
    queryKey: ["tickets", statusFilter],
    queryFn: () =>
      getTickets({
        limit: 100,
        status: statusFilter === "all" ? undefined : statusFilter,
      }),
  });

  const tickets = data?.items || [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <p className="text-muted-foreground">
          View and manage your assigned support tickets
        </p>
      </div>

      {/* Status filter tabs */}
      <Tabs
        value={statusFilter}
        onValueChange={setStatusFilter}
        className="mb-4"
      >
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="open">Open</TabsTrigger>
          <TabsTrigger value="in_progress">In Progress</TabsTrigger>
          <TabsTrigger value="resolved">Resolved</TabsTrigger>
          <TabsTrigger value="closed">Closed</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>
            {statusFilter === "all"
              ? "All Tickets"
              : `${formatStatus(statusFilter)} Tickets`}
            {data && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({data.total})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Inbox className="mb-3 h-10 w-10" />
              <p className="text-sm">
                No {statusFilter === "all" ? "" : formatStatus(statusFilter).toLowerCase() + " "}
                tickets found.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tickets.map((ticket) => (
                  <TableRow
                    key={ticket.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/agent/tickets/${ticket.id}`)}
                  >
                    <TableCell className="font-medium">#{ticket.id}</TableCell>
                    <TableCell>{ticket.customer_name || "Unknown"}</TableCell>
                    <TableCell className="max-w-[180px] truncate">
                      {ticket.conversation_title || "Untitled"}
                    </TableCell>
                    <TableCell className="max-w-[160px] truncate text-muted-foreground">
                      {ticket.reason || "—"}
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
                    <TableCell className="text-muted-foreground">
                      {formatDate(ticket.created_at)}
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
