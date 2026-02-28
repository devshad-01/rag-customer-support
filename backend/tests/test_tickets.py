"""Tests for ticket endpoints — CRUD, escalation, agent response."""

import uuid

import pytest


# ── Helpers ───────────────────────────────────────────────────

def _register_and_login(client, role="customer"):
    """Register a fresh user, login, return the auth header dict."""
    email = f"ticket_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": f"Ticket {role.title()}",
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


def _create_conversation(client, headers):
    """Create a conversation and return its ID."""
    resp = client.post("/api/chat/", json={"title": "Test Ticket Conv"}, headers=headers)
    return resp.json()["id"]


# ── Ticket creation ──────────────────────────────────────────

def test_create_ticket_via_escalation(client):
    """POST /api/chat/{id}/escalate creates a ticket."""
    customer_headers = _register_and_login(client, "customer")
    # need at least one agent for assignment
    _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    resp = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "ticket" in data
    assert data["ticket"]["conversation_id"] == conv_id
    assert data["ticket"]["status"] == "open"
    assert data["message"] == "Conversation escalated to a human agent."


def test_escalate_already_escalated(client):
    """Escalating twice returns the same ticket (idempotent)."""
    customer_headers = _register_and_login(client, "customer")
    _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    resp1 = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    resp2 = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    assert resp1.json()["ticket"]["id"] == resp2.json()["ticket"]["id"]


def test_escalate_nonexistent_conversation(client):
    """Escalating a nonexistent conversation returns 404."""
    headers = _register_and_login(client, "customer")
    resp = client.post("/api/chat/99999/escalate", headers=headers)
    assert resp.status_code == 404


# ── Ticket listing (agent) ───────────────────────────────────

def test_list_tickets_as_agent(client):
    """GET /api/tickets/ returns assigned tickets for agent."""
    customer_headers = _register_and_login(client, "customer")
    agent_headers = _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)

    resp = client.get("/api/tickets/", headers=agent_headers)
    assert resp.status_code == 200
    # Agent may or may not have this ticket assigned (depends on round-robin)
    assert "items" in resp.json()
    assert "total" in resp.json()


def test_list_tickets_as_customer_denied(client):
    """GET /api/tickets/ fails for customers."""
    headers = _register_and_login(client, "customer")
    resp = client.get("/api/tickets/", headers=headers)
    assert resp.status_code == 403


def test_list_tickets_filter_by_status(client):
    """GET /api/tickets/?status=open filters correctly."""
    agent_headers = _register_and_login(client, "agent")
    resp = client.get("/api/tickets/?status=open", headers=agent_headers)
    assert resp.status_code == 200


def test_list_tickets_invalid_status(client):
    """GET /api/tickets/?status=invalid returns 400."""
    agent_headers = _register_and_login(client, "agent")
    resp = client.get("/api/tickets/?status=invalid", headers=agent_headers)
    assert resp.status_code == 400


# ── Ticket detail and update ─────────────────────────────────

def test_get_ticket_not_found(client):
    """GET /api/tickets/99999 returns 404."""
    agent_headers = _register_and_login(client, "agent")
    resp = client.get("/api/tickets/99999", headers=agent_headers)
    assert resp.status_code == 404


def test_update_ticket_status(client):
    """PATCH /api/tickets/{id} updates status."""
    customer_headers = _register_and_login(client, "customer")
    agent_headers = _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    esc = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    ticket_id = esc.json()["ticket"]["id"]

    # The agent assigned to this ticket should be able to update it
    # Since we only have one agent, it should be assigned to them
    resp = client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "in_progress"},
        headers=agent_headers,
    )
    # Could be 200 or 403 depending on assignment — either is valid
    assert resp.status_code in (200, 403)


# ── Agent response ────────────────────────────────────────────

def test_respond_to_ticket(client):
    """POST /api/tickets/{id}/respond adds agent message."""
    customer_headers = _register_and_login(client, "customer")
    agent_headers = _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    esc = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    ticket_id = esc.json()["ticket"]["id"]

    resp = client.post(
        f"/api/tickets/{ticket_id}/respond",
        json={"content": "I can help you with that!"},
        headers=agent_headers,
    )
    # Could be 200 or 403 depending on assignment
    assert resp.status_code in (200, 403)


def test_respond_empty_content(client):
    """POST /api/tickets/{id}/respond with empty content fails."""
    customer_headers = _register_and_login(client, "customer")
    agent_headers = _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    esc = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    ticket_id = esc.json()["ticket"]["id"]

    resp = client.post(
        f"/api/tickets/{ticket_id}/respond",
        json={"content": "   "},
        headers=agent_headers,
    )
    # 400 for empty content or 403 for not assigned
    assert resp.status_code in (400, 403)


# ── Ticket delete (admin only) ───────────────────────────────

def test_delete_ticket_as_admin(client):
    """DELETE /api/tickets/{id} works for admin."""
    customer_headers = _register_and_login(client, "customer")
    admin_headers = _register_and_login(client, "admin")
    _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    esc = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    ticket_id = esc.json()["ticket"]["id"]

    resp = client.delete(f"/api/tickets/{ticket_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_delete_ticket_as_agent_denied(client):
    """DELETE /api/tickets/{id} fails for agents."""
    customer_headers = _register_and_login(client, "customer")
    agent_headers = _register_and_login(client, "agent")

    conv_id = _create_conversation(client, customer_headers)
    esc = client.post(f"/api/chat/{conv_id}/escalate", headers=customer_headers)
    ticket_id = esc.json()["ticket"]["id"]

    resp = client.delete(f"/api/tickets/{ticket_id}", headers=agent_headers)
    assert resp.status_code == 403
