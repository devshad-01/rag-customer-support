"""Pydantic schemas for analytics API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Overview ──────────────────────────────────────────────────
class OverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_queries: int = 0
    total_conversations: int = 0
    total_escalations: int = 0
    escalation_rate: float = 0.0
    avg_confidence_score: float = 0.0
    avg_response_time_ms: float = 0.0
    queries_with_evidence: int = 0
    evidence_rate: float = 0.0
    active_tickets: int = 0
    resolved_tickets: int = 0


# ── Query Trends ──────────────────────────────────────────────
class QueryTrendPoint(BaseModel):
    date: str
    query_count: int = 0
    escalation_count: int = 0


class QueryTrendsResponse(BaseModel):
    trends: list[QueryTrendPoint] = []
    interval: str = "day"


# ── Peak Hours ────────────────────────────────────────────────
class PeakHourPoint(BaseModel):
    hour: int
    query_count: int = 0


class PeakHoursResponse(BaseModel):
    hours: list[PeakHourPoint] = []


# ── Response Performance ─────────────────────────────────────
class ConfidenceDistribution(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0


class ResponsePerformanceResponse(BaseModel):
    avg_confidence: float = 0.0
    confidence_distribution: ConfidenceDistribution = ConfidenceDistribution()
    avg_response_time_ms: float = 0.0
    avg_sources_per_response: float = 0.0


# ── Confidence Trend ──────────────────────────────────────────
class ConfidenceTrendPoint(BaseModel):
    date: str
    avg_confidence: float = 0.0


class ConfidenceTrendResponse(BaseModel):
    trends: list[ConfidenceTrendPoint] = []
    interval: str = "day"


# ── Escalation Metrics ───────────────────────────────────────
class EscalationsByReason(BaseModel):
    low_confidence: int = 0
    customer_requested: int = 0
    other: int = 0


class EscalationMetricsResponse(BaseModel):
    total_escalations: int = 0
    escalation_rate: float = 0.0
    by_reason: EscalationsByReason = EscalationsByReason()
    avg_resolution_time_hours: float | None = None
    resolved_count: int = 0
    pending_count: int = 0


# ── Escalation Trend ─────────────────────────────────────────
class EscalationTrendPoint(BaseModel):
    date: str
    escalation_count: int = 0


class EscalationTrendResponse(BaseModel):
    trends: list[EscalationTrendPoint] = []
    interval: str = "day"


# ── Agent Performance ────────────────────────────────────────
class AgentPerformanceItem(BaseModel):
    agent_id: int
    agent_name: str
    tickets_assigned: int = 0
    tickets_resolved: int = 0
    avg_resolution_time_hours: float | None = None
    pending_tickets: int = 0


class AgentPerformanceResponse(BaseModel):
    agents: list[AgentPerformanceItem] = []


# ── Top Queries ──────────────────────────────────────────────
class TopQueryItem(BaseModel):
    query_text: str
    count: int = 0
    avg_confidence: float = 0.0


class TopQueriesResponse(BaseModel):
    queries: list[TopQueryItem] = []
