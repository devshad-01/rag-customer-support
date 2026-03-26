"""Admin router for AI prompt/behavior configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.schemas.ai_config import AIConfigResponse, AIConfigUpdate
from app.services import ai_config_service

router = APIRouter(prefix="/api/ai-config", tags=["AI Config"])


@router.get("/", response_model=AIConfigResponse)
async def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    _ = current_user
    config = ai_config_service.get_or_create_config(db)
    return config


@router.put("/", response_model=AIConfigResponse)
async def update_ai_config(
    payload: AIConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    _ = current_user
    config = ai_config_service.update_config(
        db,
        system_template_extension=payload.system_template_extension,
        no_escalate_out_of_scope=payload.no_escalate_out_of_scope,
    )
    return config
