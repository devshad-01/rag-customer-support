"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI application."""
    with TestClient(app) as c:
        yield c
