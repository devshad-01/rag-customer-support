"""Documents router — upload, list, get, delete (admin only)."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.schemas.document import DocumentDeleteResponse, DocumentListResponse, DocumentResponse
from app.services import document_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Upload a PDF document. Ingestion runs in the background."""
    try:
        doc = await document_service.upload_document(db, file, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed. Check logs for details.",
        )

    # Schedule ingestion as a background task (won't block the response)
    if not settings.SKIP_INGESTION:
        background_tasks.add_task(
            document_service.run_ingestion,
            doc.id,
            doc.file_path,
        )

    return _doc_to_response(doc, db)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """List all documents (paginated)."""
    docs, total = document_service.get_documents(db, page=page, limit=limit)
    return DocumentListResponse(
        items=[_doc_to_response(d, db) for d in docs],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Get a single document by ID."""
    doc = document_service.get_document_by_id(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _doc_to_response(doc, db)


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete a document (DB + Qdrant + file)."""
    try:
        document_service.delete_document(db, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return DocumentDeleteResponse(detail="Document deleted", document_id=document_id)


# ── Helpers ──────────────────────────────────────────────────

def _doc_to_response(doc, db) -> DocumentResponse:
    """Convert a Document ORM object to a response schema with chunk_count."""
    from app.models.document import DocumentChunk

    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        file_path=doc.file_path,
        file_size=doc.file_size,
        page_count=doc.page_count,
        status=doc.status.value,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunk_count=chunk_count,
    )
