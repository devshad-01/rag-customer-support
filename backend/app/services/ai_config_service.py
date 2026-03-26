"""Service layer for AI behavior config."""

from sqlalchemy.orm import Session

from app.models.ai_config import AIConfig


DEFAULT_OUT_OF_SCOPE_RESPONSE = (
    "I can help best with questions about our products and services. "
    "If you want, our team can add more company content so I can support questions like this better."
)


def get_or_create_config(db: Session) -> AIConfig:
    config = db.query(AIConfig).order_by(AIConfig.id.asc()).first()
    if config:
        return config

    config = AIConfig(
        system_template_extension="",
        out_of_scope_response=DEFAULT_OUT_OF_SCOPE_RESPONSE,
        no_escalate_out_of_scope=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_config(
    db: Session,
    *,
    system_template_extension: str,
    no_escalate_out_of_scope: bool,
) -> AIConfig:
    config = get_or_create_config(db)
    config.system_template_extension = (system_template_extension or "").strip()
    config.no_escalate_out_of_scope = bool(no_escalate_out_of_scope)
    db.commit()
    db.refresh(config)
    return config
