"""Document service — upload, ingest, list, delete."""

import logging
import os
import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.rag.vector_store import delete_document_vectors

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}


def _upload_dir() -> Path:
    """Ensure the upload directory exists and return its Path."""
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def upload_document(db: Session, file: UploadFile, user_id: int) -> Document:
    """Save uploaded PDF and create DB record (status=processing).

    This returns immediately — ingestion runs separately via run_ingestion().
    """
    # Validate
    filename = file.filename or "upload.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Only PDF files are allowed (got {ext})")

    # Save to disk
    upload_path = _upload_dir() / filename
    counter = 1
    while upload_path.exists():
        stem = os.path.splitext(filename)[0]
        upload_path = _upload_dir() / f"{stem}_{counter}{ext}"
        counter += 1

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = upload_path.stat().st_size

    # If ingestion is skipped, mark as indexed immediately (no embeddings)
    initial_status = DocumentStatus.processing
    if settings.SKIP_INGESTION:
        initial_status = DocumentStatus.indexed
        logger.info("SKIP_INGESTION=true — document will be saved without embedding")

    doc = Document(
        title=filename,
        file_path=str(upload_path),
        file_size=file_size,
        status=initial_status,
        uploaded_by=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Document id=%d saved to %s", doc.id, upload_path)
    return doc


def run_ingestion(document_id: int, file_path: str) -> None:
    """Run the RAG ingestion pipeline in a background task.

    Uses its own DB session so it's independent of the request lifecycle.
    This is safe to crash without affecting the running server.
    """
    from app.database import SessionLocal
    from app.rag.ingestion import ingest_document

    db = SessionLocal()
    try:
        result = ingest_document(document_id, file_path)

        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc is None:
            logger.error("Document id=%d not found after ingestion", document_id)
            return

        # Save chunks to DB
        for i, point_id in enumerate(result["point_ids"]):
            chunk_data = result["chunks"][i]
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                chunk_text=chunk_data["text"],
                page_number=chunk_data.get("page_number"),
                embedding_id=point_id,
            )
            db.add(chunk)

        doc.page_count = result["page_count"]
        doc.status = DocumentStatus.indexed
        db.commit()
        logger.info("Document id=%d ingested: %d chunks", document_id, result["chunk_count"])

    except Exception as exc:
        logger.error("Ingestion failed for document id=%d: %s", document_id, exc)
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = DocumentStatus.failed
                db.commit()
        except Exception:
            pass  # DB might be unreachable too
    finally:
        db.close()


def get_documents(
    db: Session,
    *,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Document], int]:
    """Return paginated list of documents with chunk counts."""
    total = db.query(Document).count()
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return docs, total


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    """Fetch a single document by ID."""
    return db.query(Document).filter(Document.id == document_id).first()


def delete_document(db: Session, document_id: int) -> None:
    """Delete document from DB, Qdrant, and disk."""
    doc = get_document_by_id(db, document_id)
    if doc is None:
        raise ValueError("Document not found")

    # Delete vectors from Qdrant (best-effort)
    try:
        delete_document_vectors(document_id)
    except Exception as exc:
        logger.warning("Failed to delete Qdrant vectors for doc %d: %s", document_id, exc)

    # Delete file from disk (best-effort)
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except OSError as exc:
        logger.warning("Failed to delete file %s: %s", doc.file_path, exc)

    # Delete from DB (chunks cascade)
    db.delete(doc)
    db.commit()
    logger.info("Deleted document id=%d", document_id)
