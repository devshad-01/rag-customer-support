"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # noqa: F401
from app.routers import auth as auth_router
from app.routers import documents as documents_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    logger.info("Starting RAG Customer Support API")

    # Auto-create tables if they don't exist (safe for production — won't drop existing)
    from app.database import engine, Base
    from app.models import user, document, conversation, ticket, query_log  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    yield
    logger.info("Shutting down RAG Customer Support API")


app = FastAPI(
    title="RAG Customer Support API",
    description="Retrieval-Augmented Generation based customer support system",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS — allow React frontend ──────────────────────────────
# Normalize origins: remove trailing slashes, deduplicate
dev_origins = {"http://localhost:5173", "http://localhost:3000", "http://localhost:8000"}
cors_origins_set = set(dev_origins)

if settings.CORS_ORIGINS:
    env_origins = [
        o.strip().rstrip("/") for o in settings.CORS_ORIGINS.split(",") 
        if o.strip()
    ]
    cors_origins_set.update(env_origins)

cors_origins = list(cors_origins_set)
logger.info(f"CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────
# Debug endpoint for CORS troubleshooting
@app.get("/api/debug/cors", tags=["Debug"])
async def debug_cors(request: Request):
    """Debug CORS configuration and incoming request headers."""
    return {
        "incoming_origin": request.headers.get("origin"),
        "allowed_origins": cors_origins,
        "cors_env_var": settings.CORS_ORIGINS,
        "request_headers": dict(request.headers),
    }

app.include_router(auth_router.router)
app.include_router(documents_router.router)


# ── Health check ──────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "service": "rag-customer-support-api"}
