import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app, get_auth_service

client = TestClient(app)

@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.decode_token = MagicMock()  # decode_token async değil, normal fonksiyon
    app.dependency_overrides[get_auth_service] = lambda: service
    yield service
    app.dependency_overrides = {}

# 1. Kayıt başarılı olmalı
def test_register_success(mock_service):
    mock_service.register.return_value = True
    response = client.post("/auth/register", json={
        "username": "emir", "password": "123", "role": "student"
    })
    assert response.status_code == 201

# 2. Kullanıcı zaten varsa 409 dönmeli
def test_register_duplicate(mock_service):
    mock_service.register.return_value = False
    response = client.post("/auth/register", json={
        "username": "emir", "password": "123", "role": "student"
    })
    assert response.status_code == 409

# 3. Giriş başarılı olmalı ve token dönmeli
def test_login_success(mock_service):
    mock_service.login.return_value = "fake-token"
    response = client.post("/auth/login", json={
        "username": "emir", "password": "123"
    })
    assert response.status_code == 200
    assert response.json()["access_token"] == "fake-token"

# 4. Yanlış şifre 401 dönmeli
def test_login_wrong_password(mock_service):
    mock_service.login.return_value = None
    response = client.post("/auth/login", json={
        "username": "emir", "password": "yanlis"
    })
    assert response.status_code == 401

# 5. Geçerli token doğrulanmalı
def test_verify_token_success(mock_service):
    mock_service.decode_token.return_value = {
        "sub": "emir", "role": "student"
    }
    response = client.get("/auth/verify", headers={
        "Authorization": "Bearer gecerli-token"
    })
    assert response.status_code == 200
    assert response.json()["role"] == "student"

# 6. Geçersiz token 401 dönmeli
def test_verify_token_invalid(mock_service):
    mock_service.decode_token.return_value = None
    response = client.get("/auth/verify", headers={
        "Authorization": "Bearer gecersiz-token"
    })
    assert response.status_code == 401

# 7. Token hiç gönderilmezse 401 dönmeli
def test_verify_no_token(mock_service):
    response = client.get("/auth/verify")
    assert response.status_code == 401
