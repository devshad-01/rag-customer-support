"""Analytics service — SQLAlchemy aggregation queries for dashboard data."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import case, cast, extract, func, Float, Integer
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.query_log import QueryLog
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def _date_filter(query, model_col, start_date: datetime | None, end_date: datetime | None):
    """Apply optional date range filter to a query."""
    if start_date:
        query = query.filter(model_col >= start_date)
    if end_date:
        query = query.filter(model_col <= end_date)
    return query


def get_overview(db: Session, start_date: datetime | None = None, end_date: datetime | None = None) -> dict:
    """Aggregate overview metrics for the admin dashboard."""
    # Query logs stats
    logs_q = db.query(QueryLog)
    logs_q = _date_filter(logs_q, QueryLog.created_at, start_date, end_date)

    total_queries = logs_q.count()
    total_escalations = logs_q.filter(QueryLog.escalated == True).count()  # noqa: E712
    escalation_rate = (total_escalations / total_queries * 100) if total_queries > 0 else 0.0

    agg = logs_q.with_entities(
        func.coalesce(func.avg(QueryLog.confidence_score), 0).label("avg_conf"),
        func.coalesce(func.avg(QueryLog.response_time_ms), 0).label("avg_rt"),
        func.sum(case((QueryLog.has_sufficient_evidence == True, 1), else_=0)).label("with_ev"),  # noqa: E712
    ).first()

    avg_confidence = float(agg.avg_conf) if agg else 0.0
    avg_response_time = float(agg.avg_rt) if agg else 0.0
    queries_with_evidence = int(agg.with_ev) if agg and agg.with_ev else 0
    evidence_rate = (queries_with_evidence / total_queries * 100) if total_queries > 0 else 0.0

    # Conversations
    convs_q = db.query(Conversation)
    convs_q = _date_filter(convs_q, Conversation.created_at, start_date, end_date)
    total_conversations = convs_q.count()

    # Tickets
    tickets_q = db.query(Ticket)
    tickets_q = _date_filter(tickets_q, Ticket.created_at, start_date, end_date)
    active_tickets = tickets_q.filter(
        Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress])
    ).count()
    resolved_tickets = tickets_q.filter(
        Ticket.status.in_([TicketStatus.resolved, TicketStatus.closed])
    ).count()

    return {
        "total_queries": total_queries,
        "total_conversations": total_conversations,
        "total_escalations": total_escalations,
        "escalation_rate": round(escalation_rate, 2),
        "avg_confidence_score": round(avg_confidence, 4),
        "avg_response_time_ms": round(avg_response_time, 1),
        "queries_with_evidence": queries_with_evidence,
        "evidence_rate": round(evidence_rate, 2),
        "active_tickets": active_tickets,
        "resolved_tickets": resolved_tickets,
    }


def get_query_trends(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    interval: str = "day",
) -> list[dict]:
    """Query count grouped by time interval."""
    # Use date_trunc for PostgreSQL; fall back to date() for SQLite
    try:
        trunc = func.date_trunc(interval, QueryLog.created_at)
    except Exception:
        trunc = func.date(QueryLog.created_at)

    q = db.query(
        trunc.label("date"),
        func.count(QueryLog.id).label("query_count"),
        func.sum(case((QueryLog.escalated == True, 1), else_=0)).label("escalation_count"),  # noqa: E712
    ).group_by(trunc).order_by(trunc)

    q = _date_filter(q, QueryLog.created_at, start_date, end_date)
    rows = q.all()

    return [
        {
            "date": str(r.date)[:10] if r.date else "",
            "query_count": int(r.query_count),
            "escalation_count": int(r.escalation_count) if r.escalation_count else 0,
        }
        for r in rows
    ]


def get_peak_hours(db: Session) -> list[dict]:
    """Query count grouped by hour of day."""
    q = db.query(
        extract("hour", QueryLog.created_at).label("hour"),
        func.count(QueryLog.id).label("query_count"),
    ).group_by("hour").order_by("hour")

    return [
        {"hour": int(r.hour), "query_count": int(r.query_count)}
        for r in q.all()
    ]


def get_response_performance(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Response performance metrics including confidence distribution."""
    q = db.query(QueryLog)
    q = _date_filter(q, QueryLog.created_at, start_date, end_date)

    total = q.count()
    if total == 0:
        return {
            "avg_confidence": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "avg_response_time_ms": 0.0,
            "avg_sources_per_response": 0.0,
        }

    agg = q.with_entities(
        func.coalesce(func.avg(QueryLog.confidence_score), 0).label("avg_conf"),
        func.coalesce(func.avg(QueryLog.response_time_ms), 0).label("avg_rt"),
        func.coalesce(func.avg(cast(QueryLog.sources_count, Float)), 0).label("avg_src"),
        func.sum(case((QueryLog.confidence_score >= 0.7, 1), else_=0)).label("high"),
        func.sum(case((
            (QueryLog.confidence_score >= 0.4) & (QueryLog.confidence_score < 0.7), 1
        ), else_=0)).label("medium"),
        func.sum(case((QueryLog.confidence_score < 0.4, 1), else_=0)).label("low"),
    ).first()

    return {
        "avg_confidence": round(float(agg.avg_conf), 4),
        "confidence_distribution": {
            "high": int(agg.high) if agg.high else 0,
            "medium": int(agg.medium) if agg.medium else 0,
            "low": int(agg.low) if agg.low else 0,
        },
        "avg_response_time_ms": round(float(agg.avg_rt), 1),
        "avg_sources_per_response": round(float(agg.avg_src), 1),
    }


def get_confidence_trend(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    interval: str = "day",
) -> list[dict]:
    """Average confidence score over time."""
    try:
        trunc = func.date_trunc(interval, QueryLog.created_at)
    except Exception:
        trunc = func.date(QueryLog.created_at)

    q = db.query(
        trunc.label("date"),
        func.avg(QueryLog.confidence_score).label("avg_confidence"),
    ).group_by(trunc).order_by(trunc)

    q = _date_filter(q, QueryLog.created_at, start_date, end_date)

    return [
        {
            "date": str(r.date)[:10] if r.date else "",
            "avg_confidence": round(float(r.avg_confidence), 4) if r.avg_confidence else 0.0,
        }
        for r in q.all()
    ]


def get_escalation_metrics(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Escalation breakdown and resolution stats."""
    # From QueryLog
    logs_q = db.query(QueryLog)
    logs_q = _date_filter(logs_q, QueryLog.created_at, start_date, end_date)

    total_queries = logs_q.count()
    total_escalations = logs_q.filter(QueryLog.escalated == True).count()  # noqa: E712
    escalation_rate = (total_escalations / total_queries * 100) if total_queries > 0 else 0.0

    # Breakdown by reason
    low_conf = logs_q.filter(
        QueryLog.escalated == True,  # noqa: E712
        QueryLog.escalation_reason.ilike("%confidence%"),
    ).count()

    customer_req = logs_q.filter(
        QueryLog.escalated == True,  # noqa: E712
        QueryLog.escalation_reason.ilike("%customer%"),
    ).count()

    other_esc = total_escalations - low_conf - customer_req

    # From Tickets
    tickets_q = db.query(Ticket)
    tickets_q = _date_filter(tickets_q, Ticket.created_at, start_date, end_date)

    resolved_q = tickets_q.filter(
        Ticket.status.in_([TicketStatus.resolved, TicketStatus.closed])
    )
    resolved_count = resolved_q.count()
    pending_count = tickets_q.filter(
        Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress])
    ).count()

    # Average resolution time (for resolved tickets with resolved_at set)
    avg_res = resolved_q.filter(Ticket.resolved_at.isnot(None)).with_entities(
        func.avg(
            extract("epoch", Ticket.resolved_at) - extract("epoch", Ticket.created_at)
        ).label("avg_seconds")
    ).first()

    avg_resolution_hours = None
    if avg_res and avg_res.avg_seconds:
        avg_resolution_hours = round(float(avg_res.avg_seconds) / 3600, 1)

    return {
        "total_escalations": total_escalations,
        "escalation_rate": round(escalation_rate, 2),
        "by_reason": {
            "low_confidence": low_conf,
            "customer_requested": customer_req,
            "other": other_esc,
        },
        "avg_resolution_time_hours": avg_resolution_hours,
        "resolved_count": resolved_count,
        "pending_count": pending_count,
    }


def get_escalation_trend(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    interval: str = "day",
) -> list[dict]:
    """Escalation count over time."""
    try:
        trunc = func.date_trunc(interval, QueryLog.created_at)
    except Exception:
        trunc = func.date(QueryLog.created_at)

    q = db.query(
        trunc.label("date"),
        func.sum(case((QueryLog.escalated == True, 1), else_=0)).label("escalation_count"),  # noqa: E712
    ).group_by(trunc).order_by(trunc)

    q = _date_filter(q, QueryLog.created_at, start_date, end_date)

    return [
        {
            "date": str(r.date)[:10] if r.date else "",
            "escalation_count": int(r.escalation_count) if r.escalation_count else 0,
        }
        for r in q.all()
    ]


def get_agent_performance(db: Session) -> list[dict]:
    """Per-agent ticket metrics."""
    agents = db.query(User).filter(User.role == UserRole.agent, User.is_active == True).all()  # noqa: E712

    result = []
    for agent in agents:
        tickets_q = db.query(Ticket).filter(Ticket.assigned_agent_id == agent.id)
        assigned = tickets_q.count()
        resolved_q = tickets_q.filter(
            Ticket.status.in_([TicketStatus.resolved, TicketStatus.closed])
        )
        resolved = resolved_q.count()
        pending = tickets_q.filter(
            Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress])
        ).count()

        # Average resolution time
        avg_res = resolved_q.filter(Ticket.resolved_at.isnot(None)).with_entities(
            func.avg(
                extract("epoch", Ticket.resolved_at) - extract("epoch", Ticket.created_at)
            ).label("avg_seconds")
        ).first()

        avg_hours = None
        if avg_res and avg_res.avg_seconds:
            avg_hours = round(float(avg_res.avg_seconds) / 3600, 1)

        result.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "tickets_assigned": assigned,
            "tickets_resolved": resolved,
            "avg_resolution_time_hours": avg_hours,
            "pending_tickets": pending,
        })

    return result


def get_top_queries(db: Session, limit: int = 10) -> list[dict]:
    """Most frequently asked questions (grouped by exact query text)."""
    rows = (
        db.query(
            QueryLog.query_text,
            func.count(QueryLog.id).label("count"),
            func.avg(QueryLog.confidence_score).label("avg_confidence"),
        )
        .group_by(QueryLog.query_text)
        .order_by(func.count(QueryLog.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "query_text": r.query_text,
            "count": int(r.count),
            "avg_confidence": round(float(r.avg_confidence), 4) if r.avg_confidence else 0.0,
        }
        for r in rows
    ]
