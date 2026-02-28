import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getConversations,
  createConversation,
  getMessages,
  sendMessage,
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
  MessageSquare,
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
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

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
            <FileText className="h-3.5 w-3.5 shrink-0 text-primary" />
            <span className="font-medium truncate">{source.title}</span>
            {source.page_number != null && (
              <span className="text-muted-foreground">Page {source.page_number}</span>
            )}
            {source.is_primary && (
              <Badge variant="default" className="text-[9px] px-1 py-0 h-4">
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
          This response may not be fully accurate. Consider contacting a support agent for assistance.
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
          isUser ? "bg-primary" : isAgent ? "bg-orange-500" : "bg-muted"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-primary-foreground" />
        ) : (
          <Bot className={cn("h-4 w-4", isAgent ? "text-white" : "text-muted-foreground")} />
        )}
      </div>
      <div className={cn("flex max-w-[75%] flex-col gap-1", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm bg-muted"
          )}
        >
          {message.content}
        </div>

        {/* Evidence warning for weak sources */}
        {!isUser && <EvidenceWarning evidence={evidence} />}

        {/* Confidence badge + timestamp row */}
        <div className="flex items-center gap-2">
          {!isUser && <ConfidenceBadge confidence={message.confidence} />}
          <span className="text-[10px] text-muted-foreground">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {/* Collapsible source section */}
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
            <FileText className="h-5 w-5 text-primary" />
            {preview?.title || "Document Preview"}
          </DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : preview ? (
          <div className="flex flex-col gap-3 overflow-y-auto pr-2">
            {/* Document metadata */}
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {preview.page_count && (
                <Badge variant="outline">{preview.page_count} pages</Badge>
              )}
              <Badge variant="outline">{preview.chunk_count} chunks</Badge>
              <Badge variant="outline">{preview.status}</Badge>
            </div>
            <Separator />
            {/* Chunks */}
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

function ConversationItem({ conv, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full rounded-md px-3 py-2 text-left text-sm transition",
        isActive
          ? "bg-primary text-primary-foreground"
          : "hover:bg-accent text-muted-foreground hover:text-accent-foreground"
      )}
    >
      <p className="truncate font-medium">{conv.title || "New chat"}</p>
      {conv.last_message && (
        <p className="mt-0.5 truncate text-xs opacity-75">
          {conv.last_message.slice(0, 60)}
        </p>
      )}
    </button>
  );
}

// ── Main Chat page ───────────────────────────────────────────

export default function Chat() {
  const [activeConvId, setActiveConvId] = useState(null);
  const [input, setInput] = useState("");
  const [optimisticMsg, setOptimisticMsg] = useState(null);
  const [previewDocId, setPreviewDocId] = useState(null);
  const queryClient = useQueryClient();
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Fetch conversations
  const { data: convData } = useQuery({
    queryKey: ["conversations"],
    queryFn: getConversations,
  });
  const conversations = convData?.items || [];

  // Fetch messages for active conversation
  const { data: messages = [], isLoading: loadingMessages } = useQuery({
    queryKey: ["messages", activeConvId],
    queryFn: () => getMessages(activeConvId),
    enabled: !!activeConvId,
  });

  // Scroll when messages update or optimistic msg changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, optimisticMsg]);

  // Create conversation
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

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    let convId = activeConvId;

    // If no active conversation, create one first
    if (!convId) {
      try {
        const conv = await createMutation.mutateAsync();
        convId = conv.id;
        setActiveConvId(convId);
      } catch {
        return;
      }
    }

    // Set optimistic user message immediately
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
    <div className="flex h-[calc(100vh-3.5rem)] flex-col md:flex-row">
      {/* ── Conversation list sidebar ── */}
      <aside className="w-full shrink-0 border-b md:w-64 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between p-3">
          <h2 className="text-sm font-semibold">Conversations</h2>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <Separator />
        <div className="flex max-h-48 flex-col gap-1 overflow-y-auto p-2 md:max-h-none md:flex-1">
          {conversations.length === 0 ? (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              No conversations yet
            </p>
          ) : (
            conversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isActive={conv.id === activeConvId}
                onClick={() => setActiveConvId(conv.id)}
              />
            ))
          )}
        </div>
      </aside>

      {/* ── Chat area ── */}
      <div className="flex flex-1 flex-col">
        {!activeConvId ? (
          /* Empty state */
          <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <MessageSquare className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Start a conversation</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Ask a question about our products and services
              </p>
            </div>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              <Plus className="mr-2 h-4 w-4" />
              New Conversation
            </Button>
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
                  <p className="py-12 text-center text-sm text-muted-foreground">
                    Send a message to get started
                  </p>
                ) : (
                  messages.map((msg) => (
                    <ChatBubble
                      key={msg.id}
                      message={msg}
                      onViewDocument={setPreviewDocId}
                    />
                  ))
                )}
                {/* Optimistic user message while waiting for API */}
                {optimisticMsg && <ChatBubble message={optimisticMsg} onViewDocument={setPreviewDocId} />}
                {isSending && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input bar */}
            <div className="border-t p-4">
              <div className="mx-auto flex max-w-3xl items-center gap-2">
                <Input
                  placeholder="Type your question..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isSending}
                  className="flex-1"
                />
                <Button
                  size="icon"
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
