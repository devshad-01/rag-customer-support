"""Qdrant vector store connection and collection setup."""

import logging

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

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
