"""Pydantic v2 schemas for ticket / escalation endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Requests ──────────────────────────────────────────────────

class TicketCreate(BaseModel):
    """Create a ticket (manual or auto-escalation)."""
    conversation_id: int
    reason: str | None = None
    priority: str = "medium"  # low | medium | high


class TicketUpdate(BaseModel):
    """Update ticket status or assignment."""
    status: str | None = None           # open | in_progress | resolved | closed
    priority: str | None = None         # low | medium | high
    assigned_agent_id: int | None = None


class TicketRespond(BaseModel):
    """Agent response to an escalated ticket."""
    content: str


# ── Responses ─────────────────────────────────────────────────

class TicketResponse(BaseModel):
    """Full ticket representation."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    customer_id: int
    assigned_agent_id: int | None = None
    status: str
    priority: str
    reason: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    updated_at: datetime | None = None
    # Computed fields filled by the router
    customer_name: str | None = None
    agent_name: str | None = None
    conversation_title: str | None = None
    message_count: int = 0


class TicketListResponse(BaseModel):
    """Paginated list of tickets."""
    items: list[TicketResponse]
    total: int


class EscalationResponse(BaseModel):
    """Response after a manual escalation."""
    ticket: TicketResponse
    message: str
