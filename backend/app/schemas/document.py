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


# ── Source verification schemas (Week 5) ──────────────────────

class ChunkResponse(BaseModel):
    """A single document chunk with context."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    page_number: int | None = None
    embedding_id: str | None = None


class ChunkWithContext(BaseModel):
    """A chunk with its surrounding context chunks."""

    chunk: ChunkResponse
    document_title: str
    previous_chunk: ChunkResponse | None = None
    next_chunk: ChunkResponse | None = None


class DocumentPreview(BaseModel):
    """Document metadata with first few chunks for preview."""

    id: int
    title: str
    file_size: int | None = None
    page_count: int | None = None
    status: str
    chunk_count: int = 0
    created_at: datetime
    chunks: list[ChunkResponse] = []
