"""Document service — upload, ingest, list, delete."""

import logging
import os
import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.rag.ingestion import ingest_document
from app.rag.vector_store import delete_document_vectors

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}


def _upload_dir() -> Path:
    """Ensure the upload directory exists and return its Path."""
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def upload_and_ingest(db: Session, file: UploadFile, user_id: int) -> Document:
    """Save uploaded PDF, create DB record, run ingestion pipeline.

    Steps:
        1. Validate file extension
        2. Save file to disk
        3. Create Document row (status=processing)
        4. Run RAG ingestion (parse → chunk → embed → store)
        5. Save DocumentChunk rows
        6. Update Document status → indexed
    """
    # Validate
    filename = file.filename or "upload.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Only PDF files are allowed (got {ext})")

    # Save to disk
    upload_path = _upload_dir() / filename
    # Avoid collisions by appending a counter
    counter = 1
    while upload_path.exists():
        stem = os.path.splitext(filename)[0]
        upload_path = _upload_dir() / f"{stem}_{counter}{ext}"
        counter += 1

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = upload_path.stat().st_size

    # Create DB record
    doc = Document(
        title=filename,
        file_path=str(upload_path),
        file_size=file_size,
        status=DocumentStatus.processing,
        uploaded_by=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Document id=%d saved to %s", doc.id, upload_path)

    # Ingest
    try:
        result = ingest_document(doc.id, str(upload_path))

        # Save chunks to DB
        for i, point_id in enumerate(result["point_ids"]):
            chunk_data = result["chunks"][i]
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                chunk_text=chunk_data["text"],
                page_number=chunk_data.get("page_number"),
                embedding_id=point_id,
            )
            db.add(chunk)

        doc.page_count = result["page_count"]
        doc.status = DocumentStatus.indexed
        db.commit()
        db.refresh(doc)
        logger.info("Document id=%d ingested: %d chunks", doc.id, result["chunk_count"])

    except Exception as exc:
        logger.error("Ingestion failed for document id=%d: %s", doc.id, exc)
        doc.status = DocumentStatus.failed
        db.commit()
        raise

    return doc


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
