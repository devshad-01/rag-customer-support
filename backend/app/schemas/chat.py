"""Pydantic v2 schemas for chat / conversation endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Requests ──────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    """Start a new conversation."""
    title: str | None = None


class MessageCreate(BaseModel):
    """Send a message in a conversation."""
    content: str


# ── Responses ─────────────────────────────────────────────────

class SourceReference(BaseModel):
    """A single source that backs an AI response."""
    title: str
    page_number: int | None = None
    chunk_text: str = ""
    score: float = 0.0
    document_id: int | None = None
    chunk_id: str = ""
    rank: int = 0
    is_primary: bool = False


class HighlightMapping(BaseModel):
    """Maps a response segment to its source chunk."""
    chunk_id: str = ""
    document_id: int | None = None
    matched_phrases: list[str] = []
    overlap_score: float = 0.0


class EvidenceInfo(BaseModel):
    """Evidence sufficiency assessment."""
    has_sufficient_evidence: bool
    evidence_quality: str  # "strong" | "moderate" | "weak" | "none"
    disclaimer: str | None = None


class ConfidenceInfo(BaseModel):
    """Confidence metadata for an AI response."""
    confidence_score: float
    has_sufficient_evidence: bool
    escalation_action: str  # "none" | "offer" | "auto"


class MessageResponse(BaseModel):
    """A single chat message."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_role: str
    content: str
    sources: list[SourceReference] = []
    confidence: ConfidenceInfo | None = None
    evidence: EvidenceInfo | None = None
    highlights: list[HighlightMapping] = []
    created_at: datetime


class ChatResponse(BaseModel):
    """Full response after sending a message (AI reply + metadata)."""
    message: MessageResponse
    sources: list[SourceReference] = []
    confidence: ConfidenceInfo | None = None
    evidence: EvidenceInfo | None = None
    highlights: list[HighlightMapping] = []
    total_sources_found: int = 0


class ConversationResponse(BaseModel):
    """A conversation summary."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    last_message: str | None = None
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""
    items: list[ConversationResponse]
    total: int
