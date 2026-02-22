"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # noqa: F401
from app.routers import auth as auth_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    logger.info("Starting RAG Customer Support API")
    yield
    logger.info("Shutting down RAG Customer Support API")


app = FastAPI(
    title="RAG Customer Support API",
    description="Retrieval-Augmented Generation based customer support system",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS — allow React frontend ──────────────────────────────
cors_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # fallback
]
if settings.CORS_ORIGINS:
    cors_origins.extend(
        [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router.router)


# ── Health check ──────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "service": "rag-customer-support-api"}
