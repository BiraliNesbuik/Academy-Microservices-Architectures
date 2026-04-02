import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app, get_course_repository

client = TestClient(app)

# Bu "fixture" veri tabanını taklit eder ve hatayı önler
@pytest.fixture(autouse=True)
def mock_repo():
    # 1. Sahte bir repository oluşturuyoruz
    repo_mock = MagicMock()
    # 2. Fonksiyonlarını asenkron (AsyncMock) olarak tanımlıyoruz
    repo_mock.create_course = AsyncMock(return_value="fake_course_id_123")
    repo_mock.get_all_courses = AsyncMock(return_value=[])
    
    # 3. FastAPI'ye diyoruz ki: "Gerçek veri tabanını değil, bu sahteyi kullan"
    app.dependency_overrides[get_course_repository] = lambda: repo_mock
    
    yield repo_mock
    
    # 4. Test bitince her şeyi eski haline getir
    app.dependency_overrides = {}

def test_create_course_success(mock_repo):
    payload = {
        "title": "İş İngilizcesi B2",
        "level": "B2",
        "price": 1500.0,
        "is_active": True
    }
    response = client.post("/courses", json=payload)
    
    # Beklenen durum: 201 Created
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["id"] == "fake_course_id_123"

def test_get_all_courses(mock_repo):
    response = client.get("/courses")
    
    # Beklenen durum: 200 OK ve bir liste dönmesi
    assert response.status_code == 200
    assert isinstance(response.json(), list)