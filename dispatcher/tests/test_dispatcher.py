import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import requests
from main import app
from jose import JWTError

@pytest.fixture(autouse=True)
def mock_db():
    mock_database = MagicMock()
    mock_collection = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.count_documents = AsyncMock(return_value=0)
    mock_database.traffic_logs = mock_collection
    app.state.db = mock_database
    yield mock_database

client = TestClient(app)

def make_mock_response(status_code, text):
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.text = text
    mock_response.content = text.encode("utf-8")
    mock_response.headers = {"content-type": "application/json"}
    return mock_response

# 1. Başarılı Yönlendirme Testi
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_route_to_exam_service_success(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.return_value = make_mock_response(200, '{"service": "exam-service"}')

    headers = {"Authorization": "Bearer gercek_gibi_token"}
    response = client.get("/exam/status", headers=headers)

    assert response.status_code == 200
    assert response.json().get("service") == "exam-service"

# 2. Token Yoksa 401 Testi
def test_unauthorized_missing_token():
    response = client.get("/exam/status")
    assert response.status_code == 401

# 3. Token Bozuksa 401 Testi
@patch('main.jwt.decode')
def test_unauthorized_invalid_token(mock_jwt):
    mock_jwt.side_effect = JWTError("Invalid token")
    headers = {"Authorization": "Bearer bozuk_token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 401

# 4. Rolün Yetkisi Yoksa 403 Testi
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_forbidden_role(mock_check, mock_jwt):
    mock_jwt.return_value = {"sub": "emir", "role": "guest"}
    mock_check.return_value = False
    headers = {"Authorization": "Bearer token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 403

# 5. 500 İç Hata Testi
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_no_200_on_error(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.return_value = make_mock_response(200, '{"error": true}')

    headers = {"Authorization": "Bearer token"}
    response = client.get("/exam/error-test", headers=headers)
    assert response.status_code == 500

# 6. 503 Servis Ölü Testi
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_503_on_dead_service(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.side_effect = requests.exceptions.ConnectionError()

    headers = {"Authorization": "Bearer token"}
    response = client.get("/exam/dead-service", headers=headers)
    assert response.status_code == 503

# 7. 504 Zaman Aşımı Testi
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_timeout(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.side_effect = requests.exceptions.Timeout()

    headers = {"Authorization": "Bearer token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 504

# 8. Course servisine başarılı yönlendirme
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_route_to_course_service_success(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.return_value = make_mock_response(200, '{"service": "course-service"}')

    headers = {"Authorization": "Bearer token"}
    response = client.get("/course/list", headers=headers)

    assert response.status_code == 200
    assert response.json().get("service") == "course-service"

# 9. Course servisine yetkisiz erişim 403 vermeli
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_course_forbidden_role(mock_check, mock_jwt):
    mock_jwt.return_value = {"sub": "emir", "role": "guest"}
    mock_check.return_value = False

    headers = {"Authorization": "Bearer token"}
    response = client.get("/course/list", headers=headers)
    assert response.status_code == 403

# 10. Course servisi ölüyse 503 vermeli
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_course_503_on_dead_service(mock_check, mock_jwt, mock_get):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.side_effect = requests.exceptions.ConnectionError()

    headers = {"Authorization": "Bearer token"}
    response = client.get("/course/dead", headers=headers)
    assert response.status_code == 503

# 11. Olmayan route 404 vermeli
def test_invalid_route():
    response = client.get("/biratyerde")
    assert response.status_code == 404

# 12. Loglama testi
@patch('main.requests.get')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_request_logging(mock_check, mock_jwt, mock_get, caplog):
    import logging
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_get.return_value = make_mock_response(200, '{}')

    with caplog.at_level(logging.INFO, logger="dispatcher"):
        client.get("/exam/status", headers={"Authorization": "Bearer token"})

    assert any("iste" in r.message.lower() or "request" in r.message.lower()
           for r in caplog.records)

# 13. Exam servisine POST isteği başarılı olmalı
@patch('main.requests.post')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_post_to_exam_service_success(mock_check, mock_jwt, mock_post):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_post.return_value = make_mock_response(201, '{"message": "sinav olusturuldu"}')

    headers = {"Authorization": "Bearer token"}
    payload = {"title": "Deneme Sınavı", "duration": 60}
    response = client.post("/exam/create", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json().get("message") is not None

# 14. Course servisine POST isteği başarılı olmalı
@patch('main.requests.post')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_post_to_course_service_success(mock_check, mock_jwt, mock_post):
    mock_jwt.return_value = {"sub": "emir", "role": "teacher"}
    mock_check.return_value = True
    mock_post.return_value = make_mock_response(201, '{"message": "ders olusturuldu"}')

    headers = {"Authorization": "Bearer token"}
    payload = {"title": "İngilizce A1", "price": 199}
    response = client.post("/course/create", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json().get("message") is not None

# 15. Auth servisine register yönlendirmesi başarılı olmalı
@patch('main.requests.post')
def test_route_to_auth_register(mock_post):
    mock_post.return_value = make_mock_response(201, '{"message": "Kayıt başarılı"}')

    payload = {"username": "yeni_ogrenci", "password": "123", "role": "student"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json().get("message") == "Kayıt başarılı"

# 16. Auth servisine login yönlendirmesi başarılı olmalı
@patch('main.requests.post')
def test_route_to_auth_login(mock_post):
    mock_post.return_value = make_mock_response(200, '{"access_token": "token123", "token_type": "bearer"}')

    payload = {"username": "yeni_ogrenci", "password": "123"}
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert "access_token" in response.json()

# 17. MongoDB Loglama Testi
@pytest.mark.asyncio
async def test_dispatcher_logs_traffic_to_mongo():
    from main import get_log_count, app

    app.state.db.traffic_logs.count_documents.return_value = 0
    initial_count = await get_log_count()

    client.post("/auth/login", json={"username": "test", "password": "123"})

    app.state.db.traffic_logs.insert_one.assert_called_once()

# 18. Satın alma başarılı yönlendirilmeli
@patch('main.requests.post')
@patch('main.jwt.decode')
@patch('main.check_permission', new_callable=AsyncMock)
def test_purchase_course_routed_success(mock_check, mock_jwt, mock_post):
    mock_jwt.return_value = {"sub": "emir", "role": "student"}
    mock_check.return_value = True
    mock_post.return_value = make_mock_response(201, '{"message": "Satın alma başarılı"}')

    headers = {"Authorization": "Bearer token"}
    response = client.post(
        "/course/courses/fake_id/purchase",
        json={"username": "emir", "course_id": "fake_id"},
        headers=headers
    )
    assert response.status_code == 201

# 19. Yetkisiz satın alma 401 dönmeli
def test_purchase_course_unauthorized():
    response = client.post(
        "/course/courses/fake_id/purchase",
        json={"username": "emir", "course_id": "fake_id"}
    )
    assert response.status_code == 401