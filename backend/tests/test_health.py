"""Basic health check test."""


def test_health_check(client):
    """Verify the API health endpoint is working."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rag-customer-support-api"
