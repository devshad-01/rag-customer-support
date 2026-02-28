"""Qdrant vector store connection and collection setup."""

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.config import settings

logger = logging.getLogger(__name__)

VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension


def get_qdrant_client() -> QdrantClient:
    """Create and return a Qdrant client instance."""
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection_exists(client: QdrantClient | None = None) -> None:
    """Create the Qdrant collection if it doesn't already exist."""
    client = client or get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION

    try:
        client.get_collection(collection_name)
        logger.info("Qdrant collection '%s' already exists", collection_name)
    except (UnexpectedResponse, Exception):
        logger.info("Creating Qdrant collection '%s' (vector_size=%d)", collection_name, VECTOR_SIZE)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Qdrant collection '%s' created successfully", collection_name)


def check_qdrant_health(client: QdrantClient | None = None) -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = client or get_qdrant_client()
        client.get_collections()
        return True
    except Exception:
        return False


# ── Store / Delete / Search operations ────────────────────────

def store_embeddings(
    document_id: int,
    chunks: list[dict],
    embeddings: list[list[float]],
    source_title: str = "",
    client: QdrantClient | None = None,
) -> list[str]:
    """Store chunk embeddings in Qdrant.

    Args:
        document_id: DB document id (stored in payload for filtering).
        chunks: List of dicts with 'text', 'index', 'page_number' keys.
        embeddings: Corresponding embedding vectors.
        source_title: Document title for explainability/source references.

    Returns:
        List of Qdrant point IDs (UUID strings).
    """
    client = client or get_qdrant_client()
    ensure_collection_exists(client)

    points = []
    point_ids: list[str] = []
    for chunk, embedding in zip(chunks, embeddings):
        point_id = str(uuid.uuid4())
        point_ids.append(point_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk["index"],
                    "chunk_text": chunk["text"],
                    "page_number": chunk.get("page_number"),
                    "source_title": source_title,
                },
            )
        )

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points[i : i + batch_size],
        )

    logger.info("Stored %d embeddings for document_id=%d", len(points), document_id)
    return point_ids


def delete_document_vectors(document_id: int, client: QdrantClient | None = None) -> None:
    """Delete all vectors belonging to a specific document."""
    client = client or get_qdrant_client()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )
    logger.info("Deleted vectors for document_id=%d", document_id)


def search_similar(
    query_embedding: list[float],
    top_k: int = 5,
    client: QdrantClient | None = None,
) -> list[dict]:
    """Search for the most similar chunks to a query embedding.

    Returns list of dicts with 'score', 'chunk_text', 'document_id',
    'chunk_index', 'page_number'.  Returns empty list on failure.
    """
    try:
        client = client or get_qdrant_client()
        ensure_collection_exists(client)
        results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=top_k,
        )
        return [
            {
                "score": hit.score,
                "chunk_id": str(hit.id),
                "chunk_text": hit.payload.get("chunk_text", ""),
                "document_id": hit.payload.get("document_id"),
                "chunk_index": hit.payload.get("chunk_index"),
                "page_number": hit.payload.get("page_number"),
                "source_title": hit.payload.get("source_title", ""),
            }
            for hit in results
        ]
    except Exception as exc:
        logger.error("Qdrant search failed: %s", exc)
        return []
