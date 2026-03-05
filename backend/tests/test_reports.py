"""Tests for reports endpoints — admin-only CSV/PDF export."""

import uuid

import pytest


# ── Helpers ───────────────────────────────────────────────────

def _register_and_login(client, role="customer"):
    """Register a fresh user, login, return the auth header dict."""
    email = f"reports_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": f"Reports {role.title()}",
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


# ═══════════════════════════════════════════════════════════════
#  Access Control
# ═══════════════════════════════════════════════════════════════

def test_query_logs_requires_auth(client):
    """Unauthenticated requests should be rejected."""
    resp = client.get("/api/reports/query-logs")
    assert resp.status_code in (401, 403)


def test_query_logs_rejects_customer(client):
    """Customers cannot access reports."""
    headers = _register_and_login(client, "customer")
    resp = client.get("/api/reports/query-logs", headers=headers)
    assert resp.status_code == 403


def test_query_logs_rejects_agent(client):
    """Agents cannot access reports."""
    headers = _register_and_login(client, "agent")
    resp = client.get("/api/reports/query-logs", headers=headers)
    assert resp.status_code == 403


def test_analytics_pdf_requires_auth(client):
    """Unauthenticated requests should be rejected for PDF."""
    resp = client.get("/api/reports/analytics")
    assert resp.status_code in (401, 403)


def test_escalations_rejects_customer(client):
    """Customers cannot access escalation reports."""
    headers = _register_and_login(client, "customer")
    resp = client.get("/api/reports/escalations", headers=headers)
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════
#  CSV Downloads
# ═══════════════════════════════════════════════════════════════

def test_query_logs_csv_download(client):
    """GET /api/reports/query-logs returns CSV with correct headers."""
    admin = _register_and_login(client, "admin")
    resp = client.get("/api/reports/query-logs", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "content-disposition" in resp.headers
    assert "query_logs" in resp.headers["content-disposition"]
    # CSV should have header row at minimum
    lines = resp.text.strip().split("\n")
    assert len(lines) >= 1
    assert "ID" in lines[0]
    assert "Confidence" in lines[0]


def test_query_logs_csv_with_dates(client):
    """Query logs CSV accepts optional date range."""
    admin = _register_and_login(client, "admin")
    resp = client.get(
        "/api/reports/query-logs",
        params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        headers=admin,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"


def test_escalation_csv_download(client):
    """GET /api/reports/escalations?format=csv returns CSV."""
    admin = _register_and_login(client, "admin")
    resp = client.get(
        "/api/reports/escalations",
        params={"format": "csv"},
        headers=admin,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "escalations" in resp.headers["content-disposition"]
    lines = resp.text.strip().split("\n")
    assert "Ticket ID" in lines[0]


def test_agent_performance_csv_download(client):
    """GET /api/reports/agent-performance returns CSV."""
    admin = _register_and_login(client, "admin")
    resp = client.get("/api/reports/agent-performance", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "agent_performance" in resp.headers["content-disposition"]
    lines = resp.text.strip().split("\n")
    assert "Agent ID" in lines[0]


def test_analytics_summary_csv_download(client):
    """GET /api/reports/analytics-summary returns CSV."""
    admin = _register_and_login(client, "admin")
    resp = client.get("/api/reports/analytics-summary", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "analytics_summary" in resp.headers["content-disposition"]
    text = resp.text
    assert "Overview Metrics" in text
    assert "Total Queries" in text


# ═══════════════════════════════════════════════════════════════
#  PDF Downloads
# ═══════════════════════════════════════════════════════════════

def test_analytics_pdf_download(client):
    """GET /api/reports/analytics returns a PDF file."""
    admin = _register_and_login(client, "admin")
    resp = client.get("/api/reports/analytics", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "analytics_report" in resp.headers["content-disposition"]
    # PDF magic bytes
    assert resp.content[:4] == b"%PDF"


def test_analytics_pdf_with_dates(client):
    """Analytics PDF accepts optional date range."""
    admin = _register_and_login(client, "admin")
    resp = client.get(
        "/api/reports/analytics",
        params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        headers=admin,
    )
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_escalation_pdf_download(client):
    """GET /api/reports/escalations?format=pdf returns a PDF file."""
    admin = _register_and_login(client, "admin")
    resp = client.get(
        "/api/reports/escalations",
        params={"format": "pdf"},
        headers=admin,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "escalation_report" in resp.headers["content-disposition"]
    assert resp.content[:4] == b"%PDF"
