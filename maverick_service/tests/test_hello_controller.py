"""Tests for hello world controller."""

from fastapi.testclient import TestClient

from maverick_service.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_hello_get():
    """Test GET /api/hello endpoint with query parameter."""
    response = client.get("/api/hello?name=World")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, World!"
    assert data["name"] == "World"


def test_hello_get_custom_name():
    """Test GET /api/hello with custom name."""
    response = client.get("/api/hello?name=FastAPI")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, FastAPI!"
    assert data["name"] == "FastAPI"


def test_hello_get_missing_name():
    """Test GET /api/hello without name parameter."""
    response = client.get("/api/hello")
    assert response.status_code == 422  # Unprocessable Entity


def test_hello_post():
    """Test POST /api/hello endpoint with payload."""
    response = client.post("/api/hello", json={"name": "World"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, World!"
    assert data["name"] == "World"


def test_hello_post_custom_name():
    """Test POST /api/hello with custom name."""
    response = client.post("/api/hello", json={"name": "FastAPI"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, FastAPI!"
    assert data["name"] == "FastAPI"


def test_hello_post_missing_name():
    """Test POST /api/hello without name in payload."""
    response = client.post("/api/hello", json={})
    assert response.status_code == 422  # Unprocessable Entity
