import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


from app.main import app

client = TestClient(app)

# 1. Kayıt testi: yeni kullanıcı kayıt
def test_register_success():
    payload = {
        "username": "emir",
        "password": "sifre123",
        "role": "student"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

# 2. Giriş testi: doğru bilgilerle token alınabilmeli
def test_login_success():
    payload = {
        "username": "emir",
        "password": "sifre123"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()

# 3. Yanlış şifreyle giriş 401 verecek
def test_login_wrong_password():
    payload = {
        "username": "emir",
        "password": "yanlis_sifre"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401

# 4. Token doğrulama: geçerli token kabulu
def test_verify_token_success():
    headers = {"Authorization": "Bearer gecerli_token"}
    response = client.get("/auth/verify", headers=headers)
    assert response.status_code == 200
    assert "role" in response.json()

# 5. Geçersiz token reddi
def test_verify_token_invalid():
    headers = {"Authorization": "Bearer gecersiz_token"}
    response = client.get("/auth/verify", headers=headers)
    assert response.status_code == 401