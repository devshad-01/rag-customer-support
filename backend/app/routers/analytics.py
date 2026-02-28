"""Analytics router — Admin-only dashboard data endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AgentPerformanceResponse,
    ConfidenceTrendResponse,
    EscalationMetricsResponse,
    EscalationTrendResponse,
    OverviewResponse,
    PeakHoursResponse,
    QueryTrendsResponse,
    ResponsePerformanceResponse,
    TopQueriesResponse,
)
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ── Helper: parse optional date strings ──────────────────────
def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# ── Overview ─────────────────────────────────────────────────
@router.get("/overview", response_model=OverviewResponse)
async def overview(
    start_date: str | None = Query(None, description="ISO 8601 start date"),
    end_date: str | None = Query(None, description="ISO 8601 end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> OverviewResponse:
    """Aggregated overview metrics for the admin dashboard."""
    data = analytics_service.get_overview(db, _parse_date(start_date), _parse_date(end_date))
    return OverviewResponse(**data)


# ── Query Trends ─────────────────────────────────────────────
@router.get("/query-trends", response_model=QueryTrendsResponse)
async def query_trends(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    interval: str = Query("day", description="day | week | month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> QueryTrendsResponse:
    """Query count grouped by time interval."""
    trends = analytics_service.get_query_trends(
        db, _parse_date(start_date), _parse_date(end_date), interval
    )
    return QueryTrendsResponse(trends=trends, interval=interval)


# ── Peak Hours ───────────────────────────────────────────────
@router.get("/peak-hours", response_model=PeakHoursResponse)
async def peak_hours(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> PeakHoursResponse:
    """Query count grouped by hour of day."""
    hours = analytics_service.get_peak_hours(db)
    return PeakHoursResponse(hours=hours)


# ── Response Performance ─────────────────────────────────────
@router.get("/response-performance", response_model=ResponsePerformanceResponse)
async def response_performance(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> ResponsePerformanceResponse:
    """Confidence distribution and response time stats."""
    data = analytics_service.get_response_performance(
        db, _parse_date(start_date), _parse_date(end_date)
    )
    return ResponsePerformanceResponse(**data)


# ── Confidence Trend ─────────────────────────────────────────
@router.get("/confidence-trend", response_model=ConfidenceTrendResponse)
async def confidence_trend(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    interval: str = Query("day"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> ConfidenceTrendResponse:
    """Average confidence score over time."""
    trends = analytics_service.get_confidence_trend(
        db, _parse_date(start_date), _parse_date(end_date), interval
    )
    return ConfidenceTrendResponse(trends=trends, interval=interval)


# ── Escalation Metrics ───────────────────────────────────────
@router.get("/escalations", response_model=EscalationMetricsResponse)
async def escalation_metrics(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> EscalationMetricsResponse:
    """Escalation breakdown and resolution stats."""
    data = analytics_service.get_escalation_metrics(
        db, _parse_date(start_date), _parse_date(end_date)
    )
    return EscalationMetricsResponse(**data)


# ── Escalation Trend ────────────────────────────────────────
@router.get("/escalation-trend", response_model=EscalationTrendResponse)
async def escalation_trend(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    interval: str = Query("day"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> EscalationTrendResponse:
    """Escalation count over time."""
    trends = analytics_service.get_escalation_trend(
        db, _parse_date(start_date), _parse_date(end_date), interval
    )
    return EscalationTrendResponse(trends=trends, interval=interval)


# ── Agent Performance ────────────────────────────────────────
@router.get("/agents", response_model=AgentPerformanceResponse)
async def agent_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> AgentPerformanceResponse:
    """Per-agent ticket metrics."""
    agents = analytics_service.get_agent_performance(db)
    return AgentPerformanceResponse(agents=agents)


# ── Top Queries ──────────────────────────────────────────────
@router.get("/top-queries", response_model=TopQueriesResponse)
async def top_queries(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> TopQueriesResponse:
    """Most frequently asked questions."""
    queries = analytics_service.get_top_queries(db, limit)
    return TopQueriesResponse(queries=queries)
