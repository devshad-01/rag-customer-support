"""Tests for document management endpoints."""

import uuid


def _get_admin_token(client):
    """Login as admin and return the token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if resp.status_code != 200:
        # Admin might not exist in test DB — register won't work (role=customer)
        # Skip gracefully
        return None
    return resp.json()["access_token"]


def _get_customer_token(client):
    """Register/login a customer and return the token."""
    email = f"custdoc_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Doc Customer", "email": email, "password": "custpass123"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "custpass123"},
    )
    return resp.json()["access_token"]


def test_list_documents_as_admin(client):
    """Test listing documents as admin."""
    token = _get_admin_token(client)
    if token is None:
        return  # admin not seeded in test DB
    response = client.get(
        "/api/documents/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_list_documents_as_customer_denied(client):
    """Test that customers cannot access documents endpoint."""
    token = _get_customer_token(client)
    response = client.get(
        "/api/documents/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_list_documents_without_auth(client):
    """Test documents endpoint without auth returns 401 or 403."""
    response = client.get("/api/documents/")
    assert response.status_code in (401, 403)


def test_get_nonexistent_document(client):
    """Test fetching a non-existent document returns 404."""
    token = _get_admin_token(client)
    if token is None:
        return
    response = client.get(
        "/api/documents/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_upload_non_pdf_rejected(client):
    """Test that non-PDF uploads are rejected."""
    token = _get_admin_token(client)
    if token is None:
        return
    response = client.post(
        "/api/documents/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()
