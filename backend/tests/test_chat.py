"""Tests for chat endpoints — conversations and messages."""

import uuid

import pytest


# ── Helpers ───────────────────────────────────────────────────

def _register_and_login(client, role="customer"):
    """Register a fresh user, login, return the auth header dict."""
    email = f"chat_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": "Chat Tester",
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


# ── Conversation CRUD ─────────────────────────────────────────

def test_create_conversation(client):
    """POST /api/chat/ creates a new conversation."""
    headers = _register_and_login(client)
    resp = client.post("/api/chat/", json={"title": None}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert "id" in data
    assert data["message_count"] == 0


def test_list_conversations_empty(client):
    """GET /api/chat/ returns empty list for fresh user."""
    headers = _register_and_login(client)
    resp = client.get("/api/chat/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_conversations_after_create(client):
    """GET /api/chat/ returns the conversation just created."""
    headers = _register_and_login(client)
    client.post("/api/chat/", json={"title": "My chat"}, headers=headers)
    resp = client.get("/api/chat/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "My chat"


# ── Messages ──────────────────────────────────────────────────

def test_send_message_returns_ai_response(client):
    """POST /api/chat/{id}/message returns an AI response with sources/confidence."""
    headers = _register_and_login(client)
    conv = client.post("/api/chat/", json={"title": None}, headers=headers).json()

    resp = client.post(
        f"/api/chat/{conv['id']}/message",
        json={"content": "What is your return policy?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should have a message with AI content
    assert "message" in data
    assert data["message"]["sender_role"] == "ai"
    assert len(data["message"]["content"]) > 0
    # Should have confidence info
    assert "confidence" in data
    assert "confidence_score" in data["confidence"]
    assert "escalation_action" in data["confidence"]


def test_send_message_sets_conversation_title(client):
    """First message auto-sets the conversation title."""
    headers = _register_and_login(client)
    conv = client.post("/api/chat/", json={"title": None}, headers=headers).json()
    assert conv["title"] is None

    client.post(
        f"/api/chat/{conv['id']}/message",
        json={"content": "How do I reset my password?"},
        headers=headers,
    )

    # Fetch conversations — title should now be set
    convs = client.get("/api/chat/", headers=headers).json()
    assert convs["items"][0]["title"] is not None
    assert "reset" in convs["items"][0]["title"].lower()


def test_get_messages_history(client):
    """GET /api/chat/{id}/messages returns user + AI messages in order."""
    headers = _register_and_login(client)
    conv = client.post("/api/chat/", json={"title": None}, headers=headers).json()

    client.post(
        f"/api/chat/{conv['id']}/message",
        json={"content": "Hello"},
        headers=headers,
    )

    resp = client.get(f"/api/chat/{conv['id']}/messages", headers=headers)
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) >= 2  # at least user + AI
    assert messages[0]["sender_role"] == "customer"
    assert messages[1]["sender_role"] == "ai"


# ── Access control ────────────────────────────────────────────

def test_send_message_to_nonexistent_conversation(client):
    """POST to a non-existent conversation returns 404."""
    headers = _register_and_login(client)
    resp = client.post(
        "/api/chat/99999/message",
        json={"content": "hello"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_get_messages_nonexistent_conversation(client):
    """GET messages for non-existent conversation returns 404."""
    headers = _register_and_login(client)
    resp = client.get("/api/chat/99999/messages", headers=headers)
    assert resp.status_code == 404


def test_chat_requires_auth(client):
    """Chat endpoints require authentication."""
    resp = client.post("/api/chat/", json={"title": None})
    assert resp.status_code in (401, 403)

    resp = client.get("/api/chat/")
    assert resp.status_code in (401, 403)


def test_cannot_access_other_users_conversation(client):
    """A customer cannot see another customer's conversation."""
    headers_a = _register_and_login(client)
    headers_b = _register_and_login(client)

    conv = client.post("/api/chat/", json={"title": None}, headers=headers_a).json()

    resp = client.post(
        f"/api/chat/{conv['id']}/message",
        json={"content": "hello"},
        headers=headers_b,
    )
    assert resp.status_code == 403


def test_register_with_role(client):
    """Test registering with a specific role works."""
    email = f"agent_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={
            "name": "Agent User",
            "email": email,
            "password": "agentpass123",
            "role": "agent",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "agent"
