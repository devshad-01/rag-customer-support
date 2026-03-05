"""Reports router — Admin-only CSV and PDF export endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.services import report_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


# ── Helper: parse optional date strings ──────────────────────
def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _csv_response(content: str, filename: str) -> Response:
    """Create a CSV download response."""
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_response(content: bytes, filename: str) -> Response:
    """Create a PDF download response."""
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_filename(prefix: str, ext: str, start: str | None, end: str | None) -> str:
    """Build a descriptive filename with optional date range."""
    parts = [prefix]
    if start:
        parts.append(start.replace("-", ""))
    if end:
        parts.append(end.replace("-", ""))
    return "_".join(parts) + f".{ext}"


# ── Query Logs CSV ───────────────────────────────────────────
@router.get("/query-logs")
async def download_query_logs(
    start_date: str | None = Query(None, description="ISO 8601 start date"),
    end_date: str | None = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    """Download query logs as CSV."""
    logger.info("Admin %s exporting query logs CSV", current_user.id)
    csv_data = report_service.generate_query_log_csv(
        db, _parse_date(start_date), _parse_date(end_date),
    )
    filename = _build_filename("query_logs", "csv", start_date, end_date)
    return _csv_response(csv_data, filename)


# ── Escalations (CSV or PDF) ────────────────────────────────
@router.get("/escalations")
async def download_escalations(
    format: str = Query("csv", description="csv or pdf"),
    start_date: str | None = Query(None, description="ISO 8601 start date"),
    end_date: str | None = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    """Download escalation report as CSV or PDF."""
    logger.info("Admin %s exporting escalations (%s)", current_user.id, format)

    if format.lower() == "pdf":
        pdf_data = report_service.generate_escalation_pdf(
            db, _parse_date(start_date), _parse_date(end_date),
        )
        filename = _build_filename("escalation_report", "pdf", start_date, end_date)
        return _pdf_response(pdf_data, filename)

    csv_data = report_service.generate_escalation_csv(
        db, _parse_date(start_date), _parse_date(end_date),
    )
    filename = _build_filename("escalations", "csv", start_date, end_date)
    return _csv_response(csv_data, filename)


# ── Analytics PDF ────────────────────────────────────────────
@router.get("/analytics")
async def download_analytics(
    start_date: str | None = Query(None, description="ISO 8601 start date"),
    end_date: str | None = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    """Download a comprehensive analytics PDF report."""
    logger.info("Admin %s exporting analytics PDF", current_user.id)
    pdf_data = report_service.generate_analytics_pdf(
        db, _parse_date(start_date), _parse_date(end_date),
    )
    filename = _build_filename("analytics_report", "pdf", start_date, end_date)
    return _pdf_response(pdf_data, filename)


# ── Agent Performance CSV ────────────────────────────────────
@router.get("/agent-performance")
async def download_agent_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    """Download agent performance metrics as CSV."""
    logger.info("Admin %s exporting agent performance CSV", current_user.id)
    csv_data = report_service.generate_agent_performance_csv(db)
    return _csv_response(csv_data, "agent_performance.csv")


# ── Analytics Summary CSV ────────────────────────────────────
@router.get("/analytics-summary")
async def download_analytics_summary(
    start_date: str | None = Query(None, description="ISO 8601 start date"),
    end_date: str | None = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> Response:
    """Download analytics summary as CSV."""
    logger.info("Admin %s exporting analytics summary CSV", current_user.id)
    csv_data = report_service.generate_analytics_summary_csv(
        db, _parse_date(start_date), _parse_date(end_date),
    )
    filename = _build_filename("analytics_summary", "csv", start_date, end_date)
    return _csv_response(csv_data, filename)
