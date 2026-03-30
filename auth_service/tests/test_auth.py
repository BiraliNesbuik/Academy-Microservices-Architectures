import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app, get_auth_service

client = TestClient(app)

# Testler için sahte servis (Mock)
@pytest.fixture
def mock_service():
    service = AsyncMock()
    # FastAPI'ye gerçek servis yerine bunu kullan diyoruz
    app.dependency_overrides[get_auth_service] = lambda: service
    yield service
    app.dependency_overrides = {}

def test_register_success(mock_service):
    mock_service.register.return_value = True
    response = client.post("/auth/register", json={
        "username": "emir", "password": "123", "role": "student"
    })
    assert response.status_code == 201

def test_login_success(mock_service):
    mock_service.login.return_value = "fake-token"
    response = client.post("/auth/login", json={
        "username": "emir", "password": "123"
    })
    assert response.status_code == 200
    assert response.json()["access_token"] == "fake-token"