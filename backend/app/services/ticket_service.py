"""Ticket service — assignment, workload, escalation logic."""

import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationStatus, Message, SenderRole
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def _priority_from_confidence(confidence_score: float) -> TicketPriority:
    """Map confidence score to ticket priority."""
    if confidence_score < 0.2:
        return TicketPriority.high
    if confidence_score < 0.4:
        return TicketPriority.medium
    return TicketPriority.low


def find_least_loaded_agent(db: Session) -> User | None:
    """Find the agent with the fewest open/in-progress tickets."""
    agents = db.query(User).filter(User.role == UserRole.agent, User.is_active == True).all()
    if not agents:
        return None

    best_agent = None
    min_load = float("inf")

    for agent in agents:
        load = (
            db.query(func.count(Ticket.id))
            .filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress]),
            )
            .scalar()
        ) or 0
        if load < min_load:
            min_load = load
            best_agent = agent

    return best_agent


def create_ticket(
    db: Session,
    *,
    conversation_id: int,
    customer_id: int,
    reason: str | None = None,
    priority: str = "medium",
    confidence_score: float | None = None,
) -> Ticket:
    """Create a support ticket and auto-assign to the least-loaded agent."""
    # Determine priority
    if confidence_score is not None:
        ticket_priority = _priority_from_confidence(confidence_score)
    else:
        try:
            ticket_priority = TicketPriority(priority)
        except ValueError:
            ticket_priority = TicketPriority.medium

    # Check for existing open ticket on this conversation
    existing = (
        db.query(Ticket)
        .filter(
            Ticket.conversation_id == conversation_id,
            Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress]),
        )
        .first()
    )
    if existing:
        logger.info("Ticket already exists for conversation %d: ticket %d", conversation_id, existing.id)
        return existing

    # Auto-assign
    agent = find_least_loaded_agent(db)

    ticket = Ticket(
        conversation_id=conversation_id,
        customer_id=customer_id,
        assigned_agent_id=agent.id if agent else None,
        status=TicketStatus.open,
        priority=ticket_priority,
        reason=reason,
    )
    db.add(ticket)

    # Update conversation status to escalated
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv and conv.status == ConversationStatus.active:
        conv.status = ConversationStatus.escalated

    db.flush()
    logger.info(
        "Created ticket id=%d for conv=%d assigned_to=%s priority=%s",
        ticket.id,
        conversation_id,
        agent.id if agent else "unassigned",
        ticket_priority.value,
    )
    return ticket


def update_ticket(
    db: Session,
    ticket: Ticket,
    *,
    status: str | None = None,
    priority: str | None = None,
    assigned_agent_id: int | None = None,
) -> Ticket:
    """Update ticket fields."""
    if status:
        try:
            new_status = TicketStatus(status)
            ticket.status = new_status
            if new_status == TicketStatus.resolved:
                ticket.resolved_at = datetime.utcnow()
        except ValueError:
            pass

    if priority:
        try:
            ticket.priority = TicketPriority(priority)
        except ValueError:
            pass

    if assigned_agent_id is not None:
        # Validate agent exists
        agent = db.query(User).filter(User.id == assigned_agent_id, User.role == UserRole.agent).first()
        if agent:
            ticket.assigned_agent_id = agent.id

    db.flush()
    return ticket


def add_agent_response(
    db: Session,
    ticket: Ticket,
    agent: User,
    content: str,
) -> Message:
    """Add an agent message to the ticket's conversation."""
    msg = Message(
        conversation_id=ticket.conversation_id,
        sender_role=SenderRole.agent,
        content=content,
    )
    db.add(msg)

    # Move ticket to in_progress if still open
    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.in_progress

    db.flush()
    logger.info("Agent %d responded to ticket %d", agent.id, ticket.id)
    return msg


def get_agent_workload(db: Session, agent_id: int) -> dict:
    """Return ticket counts for an agent."""
    open_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.assigned_agent_id == agent_id, Ticket.status == TicketStatus.open)
        .scalar()
    ) or 0
    in_progress = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.assigned_agent_id == agent_id, Ticket.status == TicketStatus.in_progress)
        .scalar()
    ) or 0
    resolved = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.assigned_agent_id == agent_id, Ticket.status == TicketStatus.resolved)
        .scalar()
    ) or 0
    return {"open": open_count, "in_progress": in_progress, "resolved": resolved, "total": open_count + in_progress + resolved}
