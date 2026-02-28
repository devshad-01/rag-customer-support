import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getConversations,
  createConversation,
  getMessages,
  sendMessage,
  deleteConversation,
  clearAllConversations,
  escalateConversation,
} from "@/services/chatApi";
import { getDocumentPreview } from "@/services/documentApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Plus,
  Send,
  FileText,
  Loader2,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Eye,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  PanelLeft,
  ChevronsLeft,
  LogOut,
  Moon,
  Sun,
  Trash2,
  MoreHorizontal,
  Headset,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { SupportIQIcon } from "@/components/SupportIQLogo";

// ── Relevance progress bar ───────────────────────────────────

function RelevanceBar({ score }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70
      ? "bg-green-500"
      : pct >= 40
        ? "bg-yellow-500"
        : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 rounded-full bg-muted">
        <div
          className={cn("h-1.5 rounded-full transition-all", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] font-medium text-muted-foreground w-8 text-right">
        {pct}%
      </span>
    </div>
  );
}

// ── Source card inside collapsible section ────────────────────

function SourceCard({ source, onViewDocument }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2.5 text-left text-xs transition hover:bg-muted/50"
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 truncate">
            <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="font-medium truncate">{source.title}</span>
            {source.page_number != null && (
              <span className="text-muted-foreground">p.{source.page_number}</span>
            )}
            {source.is_primary && (
              <Badge variant="secondary" className="text-[9px] px-1.5 py-0 h-4">
                Primary
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            {expanded ? (
              <ChevronUp className="h-3 w-3 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            )}
          </div>
        </div>
        <div className="mt-1.5">
          <RelevanceBar score={source.score} />
        </div>
      </button>
      {expanded && (
        <div className="border-t px-3 py-2.5">
          <p className="whitespace-pre-wrap text-xs text-muted-foreground leading-relaxed line-clamp-6">
            {source.chunk_text}
          </p>
          {source.document_id && (
            <Button
              variant="link"
              size="sm"
              className="mt-1.5 h-auto p-0 text-xs"
              onClick={(e) => {
                e.stopPropagation();
                onViewDocument(source.document_id);
              }}
            >
              <Eye className="mr-1 h-3 w-3" />
              View Full Document
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Collapsible sources section ──────────────────────────────

function SourcesSection({ sources, onViewDocument }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-1.5 w-full">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground transition hover:bg-muted/50 hover:text-foreground"
      >
        <FileText className="h-3.5 w-3.5" />
        Sources ({sources.length})
        {open ? (
          <ChevronUp className="ml-auto h-3 w-3" />
        ) : (
          <ChevronDown className="ml-auto h-3 w-3" />
        )}
      </button>
      {open && (
        <div className="mt-1.5 flex flex-col gap-1.5">
          {sources.map((src, i) => (
            <SourceCard key={i} source={src} onViewDocument={onViewDocument} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Evidence warning banner ──────────────────────────────────

function EvidenceWarning({ evidence }) {
  if (!evidence || evidence.has_sufficient_evidence) return null;

  return (
    <div className="flex items-start gap-2 rounded-lg border border-yellow-300 bg-yellow-50 px-3 py-2 text-xs text-yellow-800 dark:border-yellow-700 dark:bg-yellow-950/40 dark:text-yellow-300">
      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <div>
        <p className="font-medium">Limited supporting evidence</p>
        <p className="mt-0.5 text-yellow-700 dark:text-yellow-400">
          This response may not be fully accurate. Consider contacting a support agent.
        </p>
      </div>
    </div>
  );
}

// ── Confidence indicator ─────────────────────────────────────

function ConfidenceBadge({ confidence }) {
  if (!confidence) return null;

  const score = confidence.confidence_score;
  const pct = Math.round(score * 100);
  const Icon = score >= 0.7 ? ShieldCheck : score >= 0.4 ? Shield : ShieldAlert;

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 text-[10px]",
        score >= 0.7
          ? "border-green-500/50 text-green-600 dark:text-green-400"
          : score >= 0.4
            ? "border-yellow-500/50 text-yellow-600 dark:text-yellow-400"
            : "border-red-500/50 text-red-600 dark:text-red-400"
      )}
    >
      <Icon className="h-3 w-3" />
      {pct}%
    </Badge>
  );
}

// ── Typing indicator ─────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        <div className="flex gap-1">
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

// ── Single message bubble ────────────────────────────────────

function ChatBubble({ message, onViewDocument }) {
  const isUser = message.sender_role === "customer";
  const isAgent = message.sender_role === "agent";
  const sources = message.sources || [];
  const evidence = message.evidence || null;

  return (
    <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-neutral-800 dark:bg-neutral-600"
            : isAgent
              ? "bg-orange-500 dark:bg-orange-600"
              : "bg-muted"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : isAgent ? (
          <Headset className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-muted-foreground" />
        )}
      </div>
      <div className={cn("flex max-w-[75%] flex-col gap-1", isUser && "items-end")}>
        {isAgent && (
          <span className="text-[10px] font-medium text-orange-600 dark:text-orange-400">
            Support Agent
          </span>
        )}
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-neutral-800 text-neutral-50 dark:bg-neutral-600 dark:text-neutral-100"
              : isAgent
                ? "rounded-tl-sm border border-orange-200 bg-orange-50 text-orange-900 dark:border-orange-800 dark:bg-orange-950/40 dark:text-orange-100"
                : "rounded-tl-sm bg-muted"
          )}
        >
          {message.content}
        </div>

        {!isUser && <EvidenceWarning evidence={evidence} />}

        <div className="flex items-center gap-2">
          {!isUser && <ConfidenceBadge confidence={message.confidence} />}
          <span className="text-[10px] text-muted-foreground">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {!isUser && (
          <SourcesSection sources={sources} onViewDocument={onViewDocument} />
        )}
      </div>
    </div>
  );
}

// ── Document preview modal ───────────────────────────────────

function DocumentPreviewModal({ documentId, open, onClose }) {
  const { data: preview, isLoading } = useQuery({
    queryKey: ["documentPreview", documentId],
    queryFn: () => getDocumentPreview(documentId),
    enabled: !!documentId && open,
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-muted-foreground" />
            {preview?.title || "Document Preview"}
          </DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : preview ? (
          <div className="flex flex-col gap-3 overflow-y-auto pr-2">
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {preview.page_count && (
                <Badge variant="outline">{preview.page_count} pages</Badge>
              )}
              <Badge variant="outline">{preview.chunk_count} chunks</Badge>
              <Badge variant="outline">{preview.status}</Badge>
            </div>
            <Separator />
            {preview.chunks?.map((chunk) => (
              <div key={chunk.id} className="rounded-lg border p-3">
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-medium">Chunk #{chunk.chunk_index}</span>
                  {chunk.page_number != null && <span>Page {chunk.page_number}</span>}
                </div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {chunk.chunk_text}
                </p>
              </div>
            ))}
            {preview.chunks?.length === 0 && (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No chunks available
              </p>
            )}
          </div>
        ) : (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Document not found
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── Conversation list sidebar item ───────────────────────────

function ConversationItem({ conv, isActive, onClick, onDelete }) {
  return (
    <div
      className={cn(
        "group relative flex items-center rounded-lg transition",
        isActive
          ? "bg-neutral-800 text-neutral-50 dark:bg-neutral-600 dark:text-neutral-100"
          : "hover:bg-muted text-muted-foreground hover:text-foreground"
      )}
    >
      <button
        onClick={onClick}
        className="flex-1 min-w-0 px-3 py-2.5 text-left text-sm"
      >
        <p className="truncate font-medium">{conv.title || "New chat"}</p>
        {conv.last_message && (
          <p className="mt-0.5 truncate text-xs opacity-60">
            {conv.last_message.slice(0, 50)}
          </p>
        )}
      </button>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(conv.id);
        }}
        className={cn(
          "mr-1.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition",
          "opacity-0 group-hover:opacity-100 focus:opacity-100",
          isActive
            ? "hover:bg-neutral-700 dark:hover:bg-neutral-500 text-neutral-300"
            : "hover:bg-muted-foreground/10 text-muted-foreground"
        )}
        title="Delete conversation"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ── Main Chat page ───────────────────────────────────────────

export default function Chat() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [activeConvId, setActiveConvId] = useState(null);
  const [input, setInput] = useState("");
  const [optimisticMsg, setOptimisticMsg] = useState(null);
  const [previewDocId, setPreviewDocId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const queryClient = useQueryClient();
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Fetch conversations (poll for real-time updates)
  const { data: convData } = useQuery({
    queryKey: ["conversations"],
    queryFn: getConversations,
    refetchInterval: 5000,
  });
  const conversations = convData?.items || [];

  // Fetch messages for active conversation (poll for agent replies)
  const { data: messages = [], isLoading: loadingMessages } = useQuery({
    queryKey: ["messages", activeConvId],
    queryFn: () => getMessages(activeConvId),
    enabled: !!activeConvId,
    refetchInterval: 5000,
  });

  useEffect(() => {
    scrollToBottom();
  }, [messages, optimisticMsg]);

  // Create conversation — prevent stacking empty ones
  const handleNewConversation = () => {
    // If the current conversation has no messages, just stay on it
    if (activeConvId && messages.length === 0) return;
    // If there's already an empty conversation in the list, switch to it
    const emptyConv = conversations.find(
      (c) => !c.last_message && c.id !== activeConvId
    );
    if (emptyConv) {
      setActiveConvId(emptyConv.id);
      return;
    }
    createMutation.mutate();
  };

  const createMutation = useMutation({
    mutationFn: () => createConversation(null),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setActiveConvId(conv.id);
    },
    onError: () => toast.error("Failed to create conversation"),
  });

  // Send message
  const sendMutation = useMutation({
    mutationFn: ({ convId, content }) => sendMessage(convId, content),
    onSuccess: () => {
      setOptimisticMsg(null);
      queryClient.invalidateQueries({ queryKey: ["messages", activeConvId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: () => {
      setOptimisticMsg(null);
      toast.error("Failed to send message");
    },
  });

  // Delete a single conversation
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteConversation(id),
    onSuccess: (_, deletedId) => {
      if (activeConvId === deletedId) setActiveConvId(null);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: () => toast.error("Failed to delete conversation"),
  });

  // Clear all conversations
  const clearAllMutation = useMutation({
    mutationFn: () => clearAllConversations(),
    onSuccess: () => {
      setActiveConvId(null);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: () => toast.error("Failed to clear conversations"),
  });

  const handleDelete = (id) => {
    deleteMutation.mutate(id);
  };

  const handleClearAll = () => {
    if (conversations.length === 0) return;
    clearAllMutation.mutate();
  };

  // Escalate to human agent
  const escalateMutation = useMutation({
    mutationFn: (conversationId) => escalateConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", activeConvId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      toast.success("Conversation escalated to a human agent");
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to escalate");
    },
  });

  const handleEscalate = () => {
    if (!activeConvId) return;
    escalateMutation.mutate(activeConvId);
  };

  // Check if the latest AI message suggests escalation
  const lastAiMessage = [...messages].reverse().find((m) => m.sender_role === "ai");
  const showEscalateButton =
    activeConvId &&
    lastAiMessage?.confidence?.escalation_action === "offer" &&
    !messages.some((m) => m.sender_role === "agent") &&
    !escalateMutation.isSuccess;

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    let convId = activeConvId;

    if (!convId) {
      try {
        const conv = await createMutation.mutateAsync();
        convId = conv.id;
        setActiveConvId(convId);
      } catch {
        return;
      }
    }

    setOptimisticMsg({
      id: "optimistic",
      sender_role: "customer",
      content: trimmed,
      created_at: new Date().toISOString(),
    });

    setInput("");
    sendMutation.mutate({ convId, content: trimmed });
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isSending = sendMutation.isPending || createMutation.isPending;

  return (
    <div className="relative flex h-screen bg-background p-3 gap-3">
      {/* ── Sidebar open button (visible when sidebar closed) ── */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute left-5 top-5 z-20 flex h-8 w-8 items-center justify-center rounded-lg border bg-background shadow-sm transition hover:bg-muted"
          title="Show sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
      )}

      {/* ── Conversation sidebar (floating) ── */}
      <aside
        className={cn(
          "shrink-0 flex flex-col rounded-2xl bg-muted/40 border transition-all duration-200",
          sidebarOpen ? "w-72" : "w-0 overflow-hidden border-0 p-0"
        )}
      >
        {/* Sidebar header */}
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

        {/* New conversation button + overflow menu */}
        <div className="flex items-center gap-1.5 px-3 pb-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 justify-start gap-2 text-xs"
            onClick={handleNewConversation}
            disabled={createMutation.isPending}
          >
            <Plus className="h-3.5 w-3.5" />
            New Conversation
          </Button>
          {conversations.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon" className="h-8 w-8 shrink-0">
                  <MoreHorizontal className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={handleClearAll}
                  disabled={clearAllMutation.isPending}
                >
                  <Trash2 className="mr-2 h-3.5 w-3.5" />
                  Clear All Conversations
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <Separator />

        {/* Conversation list — hidden scrollbar + bottom fade */}
        <div className="relative flex-1 min-h-0">
          <div className="flex h-full flex-col gap-0.5 overflow-y-auto p-2 scrollbar-hide">
            {conversations.length === 0 ? (
              <p className="px-3 py-8 text-center text-xs text-muted-foreground">
                No conversations yet
              </p>
            ) : (
              conversations.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  isActive={conv.id === activeConvId}
                  onClick={() => setActiveConvId(conv.id)}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
          {/* Bottom fade overlay */}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-muted/40 to-transparent rounded-b-lg" />
        </div>

        {/* ── User footer (fixed at bottom) ── */}
        <div className="border-t px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-neutral-800 dark:bg-neutral-600">
              <User className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium leading-tight">{user?.name}</p>
              <p className="truncate text-[11px] text-muted-foreground leading-tight">{user?.email}</p>
            </div>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground"
              onClick={toggleTheme}
              title={theme === "dark" ? "Light mode" : "Dark mode"}
            >
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={logout}
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </aside>

      {/* ── Chat area (no toolbar) ── */}
      <div className="flex flex-1 flex-col min-w-0">
        {!activeConvId ? (
          /* ── Empty state ── */
          <div className="flex flex-1 flex-col items-center justify-center gap-5 p-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
              <SupportIQIcon className="h-9 w-9" />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-tight">
                What can I help you with?
              </h2>
              <p className="mt-1.5 text-sm text-muted-foreground max-w-sm">
                Ask a question about our products and services. Answers are
                sourced directly from our knowledge base.
              </p>
            </div>

            <div className="mt-2 flex w-full max-w-lg items-center gap-2 rounded-2xl border bg-muted/30 px-3 py-2 shadow-sm transition-colors focus-within:bg-muted/50 focus-within:ring-1 focus-within:ring-ring">
              <Input
                placeholder="Type your question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && input.trim()) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                disabled={isSending}
                className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0"
              />
              <Button
                size="icon"
                className="h-8 w-8 rounded-xl"
                onClick={handleSend}
                disabled={isSending || !input.trim()}
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5" />
              <span>AI-powered</span>
              <span className="text-border">|</span>
              <FileText className="h-3.5 w-3.5" />
              <span>Source-backed</span>
              <span className="text-border">|</span>
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Human fallback</span>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mx-auto flex max-w-3xl flex-col gap-4">
                {loadingMessages ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : messages.length === 0 && !optimisticMsg ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <Bot className="h-8 w-8 text-muted-foreground/50 mb-3" />
                    <p className="text-sm text-muted-foreground">
                      Send a message to get started
                    </p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <ChatBubble
                      key={msg.id}
                      message={msg}
                      onViewDocument={setPreviewDocId}
                    />
                  ))
                )}
                {optimisticMsg && (
                  <ChatBubble message={optimisticMsg} onViewDocument={setPreviewDocId} />
                )}
                {isSending && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Escalation offer button */}
            {showEscalateButton && (
              <div className="px-4 pb-2">
                <div className="mx-auto max-w-3xl">
                  <div className="flex items-center gap-3 rounded-xl border border-orange-200 bg-orange-50 px-4 py-3 dark:border-orange-800 dark:bg-orange-950/40">
                    <Headset className="h-5 w-5 shrink-0 text-orange-600 dark:text-orange-400" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-orange-900 dark:text-orange-200">
                        Want to talk to a human agent?
                      </p>
                      <p className="text-xs text-orange-700 dark:text-orange-400">
                        Our AI might not have the best answer for this question.
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="shrink-0 border-orange-300 text-orange-700 hover:bg-orange-100 dark:border-orange-700 dark:text-orange-300 dark:hover:bg-orange-900"
                      onClick={handleEscalate}
                      disabled={escalateMutation.isPending}
                    >
                      {escalateMutation.isPending ? (
                        <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Headset className="mr-1.5 h-3.5 w-3.5" />
                      )}
                      Talk to a Human
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Input bar — seamless */}
            <div className="px-4 pb-4 pt-2">
              <div className="mx-auto flex max-w-3xl items-center gap-2 rounded-2xl border bg-muted/30 px-3 py-2 shadow-sm transition-colors focus-within:bg-muted/50 focus-within:ring-1 focus-within:ring-ring">
                <Input
                  placeholder="Type your question..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isSending}
                  className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0"
                />
                <Button
                  size="icon"
                  className="h-8 w-8 rounded-xl"
                  onClick={handleSend}
                  disabled={isSending || !input.trim()}
                >
                  {isSending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Document preview modal */}
      <DocumentPreviewModal
        documentId={previewDocId}
        open={!!previewDocId}
        onClose={() => setPreviewDocId(null)}
      />
    </div>
  );
}
