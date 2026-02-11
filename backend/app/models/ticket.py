"""Ticket model — human fallback / escalation system."""

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TicketStatus(str, enum.Enum):
    """Ticket lifecycle states."""

    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority levels."""

    low = "low"
    medium = "medium"
    high = "high"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", create_constraint=True),
        nullable=False,
        default=TicketStatus.open,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", create_constraint=True),
        nullable=False,
        default=TicketPriority.medium,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)  # escalation reason
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    conversation: Mapped["Conversation"] = relationship(  # type: ignore[name-defined]
        back_populates="tickets",
    )
    assigned_agent: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        back_populates="assigned_tickets",
        foreign_keys=[assigned_agent_id],
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status.value}>"
