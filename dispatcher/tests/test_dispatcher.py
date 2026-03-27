import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import requests
from dispatcher.main import app  # tutarlı import

client = TestClient(app)

@patch('dispatcher.main.requests.get')  # ← düzeltildi
def test_route_to_exam_service_with_mock(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"service": "exam-service", "status": "running"}
    mock_response.text = '{"service": "exam-service", "status": "running"}'
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer valid_test_token"}
    response = client.get("/exam/status", headers=headers)

    mock_get.assert_called_once_with(
        "http://exam-service:8000/status", timeout=2
    )
    assert response.status_code == 200
    assert response.json().get("service") == "exam-service"

def test_unauthorized_missing_token():
    response = client.get("/exam/status")
    assert response.status_code == 401

def test_unauthorized_wrong_token():
    headers = {"Authorization": "Bearer wrong_token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 401

@patch('dispatcher.main.requests.get')
def test_no_200_on_error(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"error": True, "message": "something failed"}
    # Dikkat: JSON'da error:true (boolean) olduğunda yakalamalı
    mock_response.text = '{"error": true}'
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer valid_test_token"}
    response = client.get("/exam/error-test", headers=headers)
    assert response.status_code == 500

@patch('dispatcher.main.requests.get')
def test_503_on_dead_service(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError()

    headers = {"Authorization": "Bearer valid_test_token"}
    response = client.get("/exam/dead-service", headers=headers)
    assert response.status_code == 503

@patch('dispatcher.main.requests.get')
def test_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout()

    headers = {"Authorization": "Bearer valid_test_token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 504

def test_invalid_route():
    headers = {"Authorization": "Bearer valid_test_token"}
    response = client.get("/random", headers=headers)
    assert response.status_code == 404

@patch('dispatcher.main.requests.get')
def test_request_logging(mock_get, caplog):
    import logging
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = '{}'
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer valid_test_token"}
    with caplog.at_level(logging.INFO, logger="dispatcher"):
        client.get("/exam/status", headers=headers)

    assert any("istek" in r.message.lower() or "request" in r.message.lower()
               for r in caplog.records)