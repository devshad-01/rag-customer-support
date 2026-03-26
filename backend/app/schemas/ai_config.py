"""Schemas for admin-editable AI behavior config."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    system_template_extension: str
    no_escalate_out_of_scope: bool
    updated_at: datetime


class AIConfigUpdate(BaseModel):
    system_template_extension: str = Field(default="", max_length=12000)
    no_escalate_out_of_scope: bool = True
