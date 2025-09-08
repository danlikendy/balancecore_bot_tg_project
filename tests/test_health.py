import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Создание тестового клиента"""
    return TestClient(app)


def test_health_check(client):
    """Тест проверки здоровья API"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
