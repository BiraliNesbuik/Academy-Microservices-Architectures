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

# 8. MongoDB Repository Kayıt Testi (TDD - Kırmızı Aşama)
@pytest.mark.asyncio
async def test_user_repository_saves_to_mongo():
    """
    Kullanıcı bilgilerinin MongoDB'ye kaydedilip kaydedilmediğini test eder.
    (TDD: Kırmızı Aşama - Henüz repository içindeki MongoDB kodları yazılmadığı için BAŞARISIZ olmalıdır.)
    """
    try:
        from app.repositories.user_repository import UserRepository
    except ImportError:
        UserRepository = None

    # 1. Kontrol: Sınıf var mı?
    assert UserRepository is not None, "UserRepository sınıfı henüz tanımlanmadı veya MongoDB metotları eksik! (TDD: Red)"

    # Sahte veritabanı (Mock) koleksiyonu oluşturuyoruz
    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_db.users = mock_collection

    # 2. Kontrol: Repository'i başlat ve kullanıcı kaydetmeyi dene
    repo = UserRepository(mock_db)
    await repo.create_user({"username": "test_ogrenci", "password": "hashed_password"})

    # 3. Kontrol: Veritabanının insert_one metodu çağrılmış mı?
    mock_collection.insert_one.assert_called_once()