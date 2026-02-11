"""User model — Admin, Agent, Customer roles."""

import enum
from datetime import datetime

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """Available user roles matching the proposal's three-tier access."""

    admin = "admin"
    agent = "agent"
    customer = "customer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
        default=UserRole.customer,
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────
    documents: Mapped[list["Document"]] = relationship(  # type: ignore[name-defined]
        back_populates="uploaded_by_user",
        foreign_keys="Document.uploaded_by",
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # type: ignore[name-defined]
        back_populates="customer",
        foreign_keys="Conversation.customer_id",
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore[name-defined]
        back_populates="assigned_agent",
        foreign_keys="Ticket.assigned_agent_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
