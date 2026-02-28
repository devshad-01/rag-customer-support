"""Tickets router — CRUD, assignment, and agent response endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.conversation import Conversation, Message
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketRespond,
    TicketResponse,
    TicketUpdate,
)
from app.services import ticket_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


# ── Helpers ───────────────────────────────────────────────────

def _ticket_to_response(ticket: Ticket, db: Session) -> TicketResponse:
    """Enrich a Ticket ORM object with computed fields."""
    # Customer name
    customer = db.query(User).filter(User.id == ticket.customer_id).first()
    customer_name = customer.name if customer else None

    # Agent name
    agent_name = None
    if ticket.assigned_agent_id:
        agent = db.query(User).filter(User.id == ticket.assigned_agent_id).first()
        agent_name = agent.name if agent else None

    # Conversation info
    conv = db.query(Conversation).filter(Conversation.id == ticket.conversation_id).first()
    conversation_title = conv.title if conv else None

    msg_count = (
        db.query(func.count(Message.id))
        .filter(Message.conversation_id == ticket.conversation_id)
        .scalar()
    ) or 0

    return TicketResponse(
        id=ticket.id,
        conversation_id=ticket.conversation_id,
        customer_id=ticket.customer_id,
        assigned_agent_id=ticket.assigned_agent_id,
        status=ticket.status.value,
        priority=ticket.priority.value,
        reason=ticket.reason,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        updated_at=ticket.updated_at,
        customer_name=customer_name,
        agent_name=agent_name,
        conversation_title=conversation_title,
        message_count=msg_count,
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a support ticket (manual escalation)."""
    # Validate conversation exists and belongs to user
    conv = db.query(Conversation).filter(Conversation.id == body.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.customer_id != current_user.id and current_user.role.value not in ("admin", "agent"):
        raise HTTPException(status_code=403, detail="Not your conversation")

    ticket = ticket_service.create_ticket(
        db,
        conversation_id=body.conversation_id,
        customer_id=conv.customer_id,
        reason=body.reason,
        priority=body.priority,
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(ticket, db)


@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    """List tickets. Agents see their assigned tickets; admins see all."""
    query = db.query(Ticket)

    # Role-based filtering
    if current_user.role == UserRole.agent:
        query = query.filter(Ticket.assigned_agent_id == current_user.id)

    # Optional filters
    if status:
        try:
            query = query.filter(Ticket.status == TicketStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if priority:
        from app.models.ticket import TicketPriority
        try:
            query = query.filter(Ticket.priority == TicketPriority(priority))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")

    total = query.count()
    tickets = (
        query
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return TicketListResponse(
        items=[_ticket_to_response(t, db) for t in tickets],
        total=total,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Access control: customer sees own, agent sees assigned, admin sees all
    if current_user.role == UserRole.customer and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your ticket")
    if current_user.role == UserRole.agent and ticket.assigned_agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ticket not assigned to you")

    return _ticket_to_response(ticket, db)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    """Update ticket status, priority, or assignment."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Agent can only update their own tickets
    if current_user.role == UserRole.agent and ticket.assigned_agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ticket not assigned to you")

    ticket = ticket_service.update_ticket(
        db,
        ticket,
        status=body.status,
        priority=body.priority,
        assigned_agent_id=body.assigned_agent_id,
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(ticket, db)


@router.post("/{ticket_id}/respond", response_model=TicketResponse)
async def respond_to_ticket(
    ticket_id: int,
    body: TicketRespond,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    """Add an agent response to the ticket's conversation."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role == UserRole.agent and ticket.assigned_agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ticket not assigned to you")

    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Response cannot be empty")

    ticket_service.add_agent_response(db, ticket, current_user, content)
    db.commit()
    db.refresh(ticket)
    logger.info("Agent %d responded to ticket %d", current_user.id, ticket_id)
    return _ticket_to_response(ticket, db)


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete a ticket (admin only)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(ticket)
    db.commit()
    logger.info("Deleted ticket id=%d by admin=%d", ticket_id, current_user.id)
