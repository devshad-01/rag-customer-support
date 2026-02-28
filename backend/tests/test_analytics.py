"""Tests for analytics endpoints — admin-only dashboard data."""

import uuid

import pytest


# ── Helpers ───────────────────────────────────────────────────

def _register_and_login(client, role="customer"):
    """Register a fresh user, login, return the auth header dict."""
    email = f"analytics_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": f"Analytics {role.title()}",
            "email": email,
            "password": "testpass123",
            "role": role,
        },
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "testpass123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Access control ───────────────────────────────────────────

def test_overview_requires_admin(client):
    """Non-admin users should be rejected from analytics."""
    customer_headers = _register_and_login(client, "customer")
    resp = client.get("/api/analytics/overview", headers=customer_headers)
    assert resp.status_code == 403


def test_overview_rejects_agent(client):
    """Agents should also be rejected from analytics."""
    agent_headers = _register_and_login(client, "agent")
    resp = client.get("/api/analytics/overview", headers=agent_headers)
    assert resp.status_code == 403


def test_overview_requires_auth(client):
    """Unauthenticated requests should be rejected."""
    resp = client.get("/api/analytics/overview")
    assert resp.status_code in (401, 403)


# ── Overview endpoint ────────────────────────────────────────

def test_overview_returns_structure(client):
    """GET /api/analytics/overview returns all expected fields."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/overview", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_queries" in data
    assert "total_conversations" in data
    assert "total_escalations" in data
    assert "escalation_rate" in data
    assert "avg_confidence_score" in data
    assert "avg_response_time_ms" in data
    assert "active_tickets" in data
    assert "resolved_tickets" in data


def test_overview_with_date_filter(client):
    """Overview accepts optional date range params."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get(
        "/api/analytics/overview",
        params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        headers=admin_headers,
    )
    assert resp.status_code == 200


# ── Query trends ─────────────────────────────────────────────

def test_query_trends_returns_structure(client):
    """GET /api/analytics/query-trends returns trends array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/query-trends", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "trends" in data
    assert "interval" in data
    assert isinstance(data["trends"], list)


def test_query_trends_accepts_interval(client):
    """Query trends accepts day/week/month interval."""
    admin_headers = _register_and_login(client, "admin")
    for interval in ("day", "week", "month"):
        resp = client.get(
            "/api/analytics/query-trends",
            params={"interval": interval},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["interval"] == interval


# ── Response performance ─────────────────────────────────────

def test_response_performance_returns_structure(client):
    """GET /api/analytics/response-performance returns confidence distribution."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/response-performance", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "avg_confidence" in data
    assert "confidence_distribution" in data
    assert "high" in data["confidence_distribution"]
    assert "medium" in data["confidence_distribution"]
    assert "low" in data["confidence_distribution"]
    assert "avg_response_time_ms" in data


# ── Confidence trend ─────────────────────────────────────────

def test_confidence_trend_returns_structure(client):
    """GET /api/analytics/confidence-trend returns trends array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/confidence-trend", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "trends" in data
    assert isinstance(data["trends"], list)


# ── Escalation metrics ───────────────────────────────────────

def test_escalation_metrics_returns_structure(client):
    """GET /api/analytics/escalations returns breakdown."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/escalations", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_escalations" in data
    assert "escalation_rate" in data
    assert "by_reason" in data
    assert "resolved_count" in data
    assert "pending_count" in data


# ── Escalation trend ─────────────────────────────────────────

def test_escalation_trend_returns_structure(client):
    """GET /api/analytics/escalation-trend returns trends array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/escalation-trend", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "trends" in data
    assert isinstance(data["trends"], list)


# ── Agent performance ────────────────────────────────────────

def test_agent_performance_returns_structure(client):
    """GET /api/analytics/agents returns agents array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/agents", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)


# ── Top queries ──────────────────────────────────────────────

def test_top_queries_returns_structure(client):
    """GET /api/analytics/top-queries returns queries array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/top-queries", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "queries" in data
    assert isinstance(data["queries"], list)


def test_top_queries_accepts_limit(client):
    """Top queries accepts a limit parameter."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get(
        "/api/analytics/top-queries",
        params={"limit": 5},
        headers=admin_headers,
    )
    assert resp.status_code == 200


# ── Peak hours ───────────────────────────────────────────────

def test_peak_hours_returns_structure(client):
    """GET /api/analytics/peak-hours returns hours array."""
    admin_headers = _register_and_login(client, "admin")
    resp = client.get("/api/analytics/peak-hours", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "hours" in data
    assert isinstance(data["hours"], list)
