"""Tests for authentication endpoints."""

import uuid


def test_register_user(client):
    """Test user registration creates a customer account."""
    email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "customer"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_email(client):
    """Test registering with an existing email returns 409."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "First", "email": email, "password": "pass12345"},
    )
    response = client.post(
        "/api/auth/register",
        json={"name": "Second", "email": email, "password": "pass12345"},
    )
    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_register_short_password(client):
    """Test registration with too-short password fails validation."""
    response = client.post(
        "/api/auth/register",
        json={"name": "Short", "email": "short@example.com", "password": "123"},
    )
    assert response.status_code == 422


def test_login_success(client):
    """Test login returns access token and user info."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": email, "password": "loginpass123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "loginpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email


def test_login_wrong_password(client):
    """Test login with wrong password returns 401."""
    email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Wrong PW", "email": email, "password": "correctpass1"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_email(client):
    """Test login with non-existent email returns 401."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@nowhere.com", "password": "whatever123"},
    )
    assert response.status_code == 401


def test_me_endpoint(client):
    """Test GET /me returns current user info."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/auth/register",
        json={"name": "Me User", "email": email, "password": "mepass12345"},
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "mepass12345"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_me_without_token(client):
    """Test GET /me without token returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
