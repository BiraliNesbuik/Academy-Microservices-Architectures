import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from app.main import app, get_course_repository

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_repo():
    repo_mock = MagicMock()
    repo_mock.create_course = AsyncMock(return_value="fake_course_id_123")
    repo_mock.get_all_courses = AsyncMock(return_value=[])
    repo_mock.get_course_by_id = AsyncMock(return_value=None)
    repo_mock.purchase_course = AsyncMock(return_value="fake_purchase_id")
    app.dependency_overrides[get_course_repository] = lambda: repo_mock
    yield repo_mock
    app.dependency_overrides = {}


# 1. Kurs oluşturma başarılı olmalı
def test_create_course_success(mock_repo):
    payload = {"title": "İş İngilizcesi B2", "level": "B2", "price": 1500.0, "is_active": True}
    response = client.post("/courses", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == "fake_course_id_123"


# 2. Kurs listesi boşken boş liste dönmeli
def test_list_courses_empty(mock_repo):
    response = client.get("/courses")
    assert response.status_code == 200
    assert response.json() == []


# 3. Kurs listesi doluyken doğru veriyi döndürmeli
def test_list_courses_with_data(mock_repo):
    mock_repo.get_all_courses.return_value = [
        {"id": "abc123", "title": "İngilizce B2", "level": "B2", "price": 299.0, "is_active": True}
    ]
    response = client.get("/courses")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "İngilizce B2"


# 4. Eksik alan gönderilirse 422 dönmeli
def test_create_course_missing_field(mock_repo):
    response = client.post("/courses", json={"title": "Eksik Kurs"})
    assert response.status_code == 422


# 5. MongoDB Repository kayıt testi
@pytest.mark.asyncio
async def test_course_repository_saves_to_mongo():
    from app.repositories.course_repository import CourseRepository
    from app.models.course import Course

    mock_db = MagicMock()
    mock_collection = AsyncMock()
    mock_collection.insert_one.return_value.inserted_id = "abc123"
    mock_db.courses = mock_collection
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)  # ← bunu ekle

    test_course = Course(title="Almanca A1", level="A1", price=199.0)
    repo = CourseRepository(mock_db)
    course_id = await repo.create_course(test_course)

    mock_collection.insert_one.assert_called_once_with(test_course.model_dump())
    assert course_id is not None


# 6. Satın alma başarılı olmalı
def test_purchase_course_success(mock_repo):
    mock_repo.get_course_by_id.return_value = {
        "id": "fake_course_id_123",
        "title": "İngilizce B2",
        "level": "B2",
        "price": 299.0,
        "is_active": True
    }
    response = client.post("/courses/fake_course_id_123/purchase", json={
        "username": "emir",
        "course_id": "fake_course_id_123"
    })
    assert response.status_code == 201
    assert response.json()["message"] == "Satın alma başarılı"


# 7. Olmayan kursa satın alma 404 dönmeli
def test_purchase_course_not_found(mock_repo):
    mock_repo.get_course_by_id.return_value = None
    response = client.post("/courses/olmayan_id/purchase", json={
        "username": "emir",
        "course_id": "olmayan_id"
    })
    assert response.status_code == 404


# 8. Pasif kursa satın alma 400 dönmeli
def test_purchase_inactive_course(mock_repo):
    mock_repo.get_course_by_id.return_value = {
        "id": "fake_course_id_123",
        "title": "İngilizce B2",
        "level": "B2",
        "price": 299.0,
        "is_active": False
    }
    response = client.post("/courses/fake_course_id_123/purchase", json={
        "username": "emir",
        "course_id": "fake_course_id_123"
    })
    assert response.status_code == 400

    # 9. Tek kurs getirme başarılı olmalı
def test_get_course_by_id_success(mock_repo):
    mock_repo.get_course_by_id.return_value = {
        "id": "fake_course_id_123",
        "title": "İngilizce B2",
        "level": "B2",
        "price": 299.0,
        "is_active": True
    }
    response = client.get("/courses/fake_course_id_123")
    assert response.status_code == 200
    assert response.json()["title"] == "İngilizce B2"


# 10. Olmayan kurs 404 dönmeli
def test_get_course_by_id_not_found(mock_repo):
    mock_repo.get_course_by_id.return_value = None
    response = client.get("/courses/olmayan_id")
    assert response.status_code == 404

    # 11. Kullanıcının satın aldığı kurslar listelenmeli
def test_get_my_purchases_success(mock_repo):
    mock_repo.get_purchases_by_username = AsyncMock(return_value=[
        {"id": "purchase_1", "username": "emir", "course_id": "fake_course_id_123"}
    ])
    response = client.get("/courses/my-purchases?username=emir")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["username"] == "emir"


# 12. Satın alması olmayan kullanıcı boş liste almalı
def test_get_my_purchases_empty(mock_repo):
    mock_repo.get_purchases_by_username = AsyncMock(return_value=[])
    response = client.get("/courses/my-purchases?username=nobody")
    assert response.status_code == 200
    assert response.json() == []