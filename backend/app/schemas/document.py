"""Pydantic v2 schemas for document endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Single document returned from API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_path: str
    file_size: int | None = None
    page_count: int | None = None
    status: str
    uploaded_by: int
    created_at: datetime
    updated_at: datetime | None = None
    chunk_count: int = 0


class DocumentListResponse(BaseModel):
    """Paginated document list."""

    items: list[DocumentResponse]
    total: int
    page: int
    limit: int


class DocumentDeleteResponse(BaseModel):
    """Confirmation after deleting a document."""

    detail: str
    document_id: int
