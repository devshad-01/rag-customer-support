import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTicket, updateTicket, respondToTicket } from "@/services/ticketApi";
import { getMessages } from "@/services/chatApi";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  ArrowLeft,
  Send,
  Loader2,
  User,
  Bot,
  Headset,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

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

function formatTime(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Chat bubble (matches customer chat style) ────────────────

function MessageBubble({ msg }) {
  const isCustomer = msg.sender_role === "customer";
  const isAgent = msg.sender_role === "agent";

  let avatarBg, avatarIcon;
  if (isCustomer) {
    avatarBg = "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300";
    avatarIcon = <User className="h-4 w-4" />;
  } else if (isAgent) {
    avatarBg =
      "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300";
    avatarIcon = <Headset className="h-4 w-4" />;
  } else {
    avatarBg =
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300";
    avatarIcon = <Bot className="h-4 w-4" />;
  }

  return (
    <div
      className={cn("flex items-start gap-3", isAgent && "flex-row-reverse")}
    >
      <Avatar className={`h-8 w-8 shrink-0 ${avatarBg}`}>
        <AvatarFallback className={avatarBg}>{avatarIcon}</AvatarFallback>
      </Avatar>
      <div
        className={cn(
          "flex max-w-[75%] flex-col gap-1",
          isAgent && "items-end"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
            isCustomer && "rounded-tl-sm bg-muted",
            isAgent &&
              "rounded-tr-sm bg-orange-500 text-white dark:bg-orange-600",
            !isCustomer &&
              !isAgent &&
              "rounded-tl-sm bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100"
          )}
        >
          {msg.content}
        </div>
        <span className="text-[10px] text-muted-foreground">
          {formatTime(msg.created_at)}
        </span>
      </div>
    </div>
  );
}

// ── Compact ticket info bar ──────────────────────────────────

function TicketInfoBar({
  ticket,
  expanded,
  onToggle,
  onStatusChange,
  statusPending,
}) {
  return (
    <div className="border-b bg-muted/30">
      {/* Collapsed: single row */}
      <div className="flex items-center gap-3 px-4 py-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-sm font-semibold shrink-0">#{ticket.id}</span>
          <Separator orientation="vertical" className="h-4" />
          <span className="text-sm truncate text-muted-foreground">
            {ticket.customer_name || "Customer"}
          </span>
          <Separator orientation="vertical" className="h-4" />
          <Badge
            variant={PRIORITY_VARIANT[ticket.priority] || "secondary"}
            className="text-[10px] px-1.5 py-0 h-5"
          >
            {ticket.priority}
          </Badge>
          <Select
            value={ticket.status}
            onValueChange={onStatusChange}
            disabled={statusPending}
          >
            <SelectTrigger className="h-7 w-[120px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <button
          onClick={onToggle}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition"
        >
          {expanded ? (
            <>
              Less <ChevronUp className="h-3 w-3" />
            </>
          ) : (
            <>
              Details <ChevronDown className="h-3 w-3" />
            </>
          )}
        </button>
      </div>

      {/* Expanded: extra details */}
      {expanded && (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1 px-4 pb-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDate(ticket.created_at)}
          </span>
          <span>
            <strong className="text-foreground">Conversation:</strong>{" "}
            {ticket.conversation_title || "Untitled"}
          </span>
          {ticket.reason && (
            <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-3 w-3" />
              {ticket.reason}
            </span>
          )}
          {ticket.agent_name && (
            <span>
              <strong className="text-foreground">Agent:</strong>{" "}
              {ticket.agent_name}
            </span>
          )}
          <span>{ticket.message_count} messages</span>
        </div>
      )}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────

export default function TicketView() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [response, setResponse] = useState("");
  const [infoExpanded, setInfoExpanded] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Fetch ticket (poll every 5s for real-time feel)
  const { data: ticket, isLoading: ticketLoading } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => getTicket(ticketId),
    refetchInterval: 5000,
  });

  // Fetch conversation messages (poll every 5s)
  const { data: messages, isLoading: messagesLoading } = useQuery({
    queryKey: ["ticketMessages", ticket?.conversation_id],
    queryFn: () => getMessages(ticket.conversation_id),
    enabled: !!ticket?.conversation_id,
    refetchInterval: 5000,
  });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Respond mutation
  const respondMutation = useMutation({
    mutationFn: (content) => respondToTicket(ticketId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({
        queryKey: ["ticketMessages", ticket?.conversation_id],
      });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      setResponse("");
      toast.success("Response sent");
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to send response");
    },
  });

  // Status update mutation
  const statusMutation = useMutation({
    mutationFn: (status) => updateTicket(ticketId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      toast.success("Status updated");
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to update status");
    },
  });

  const handleSend = (e) => {
    e?.preventDefault();
    const trimmed = response.trim();
    if (!trimmed) return;
    respondMutation.mutate(trimmed);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (ticketLoading) {
    return (
      <div className="flex h-full flex-col">
        <Skeleton className="h-12 w-full" />
        <div className="flex-1 space-y-4 p-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-3/4" />
          ))}
        </div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-10 w-10 text-muted-foreground" />
        <p className="text-muted-foreground">Ticket not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/agent/tickets")}
        >
          Back to Tickets
        </Button>
      </div>
    );
  }

  const isClosed = ticket.status === "closed" || ticket.status === "resolved";

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Top bar: back + ticket info */}
      <div className="flex items-center gap-2 border-b px-4 py-2 bg-background">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={() => navigate("/agent/tickets")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-sm font-semibold truncate flex-1">
          {ticket.conversation_title || "Escalated conversation"}
        </h1>
        <Badge
          variant={STATUS_VARIANT[ticket.status] || "secondary"}
          className="shrink-0"
        >
          {formatStatus(ticket.status)}
        </Badge>
      </div>

      {/* Compact ticket metadata */}
      <TicketInfoBar
        ticket={ticket}
        expanded={infoExpanded}
        onToggle={() => setInfoExpanded(!infoExpanded)}
        onStatusChange={(val) => statusMutation.mutate(val)}
        statusPending={statusMutation.isPending}
      />

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {messagesLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !messages || messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Bot className="h-8 w-8 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                No messages in this conversation yet
              </p>
            </div>
          ) : (
            messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input bar (or closed banner) */}
      {isClosed ? (
        <div className="border-t px-4 py-3 text-center text-sm text-muted-foreground bg-muted/30">
          This ticket is {ticket.status}. No further responses can be sent.
        </div>
      ) : (
        <div className="border-t px-4 py-3 bg-background">
          <form
            onSubmit={handleSend}
            className="mx-auto flex max-w-3xl items-center gap-2"
          >
            <Input
              placeholder="Type your response..."
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={respondMutation.isPending}
              className="flex-1"
            />
            <Button
              type="submit"
              size="icon"
              className="h-9 w-9 shrink-0"
              disabled={!response.trim() || respondMutation.isPending}
            >
              {respondMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
