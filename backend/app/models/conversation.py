"""Conversation and Message models — chat history."""

import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConversationStatus(str, enum.Enum):
    """Lifecycle of a conversation."""

    active = "active"
    escalated = "escalated"
    closed = "closed"


class SenderRole(str, enum.Enum):
    """Who sent the message."""

    customer = "customer"
    ai = "ai"
    agent = "agent"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status", create_constraint=True),
        nullable=False,
        default=ConversationStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    customer: Mapped["User"] = relationship(  # type: ignore[name-defined]
        back_populates="conversations",
        foreign_keys=[customer_id],
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore[name-defined]
        back_populates="conversation",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} customer={self.customer_id} status={self.status.value}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_role: Mapped[SenderRole] = mapped_column(
        Enum(SenderRole, name="sender_role", create_constraint=True),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of source refs
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} conv={self.conversation_id} sender={self.sender_role.value}>"
