"""AI behavior configuration editable by admin."""

from datetime import datetime

from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIConfig(Base):
    __tablename__ = "ai_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    system_template_extension: Mapped[str] = mapped_column(Text, default="")
    out_of_scope_response: Mapped[str] = mapped_column(
        Text,
        default=(
            "I can help best with questions about our products and services. "
            "If you want, our team can add more company content so I can support questions like this better."
        ),
    )
    no_escalate_out_of_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
