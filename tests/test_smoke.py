"""Tests básicos de smoke para verificar que la aplicación arranca correctamente."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_app_docs_accessible():
    """Verifica que la documentación de la API es accesible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "FastAPI" in response.text or "swagger" in response.text.lower()


def test_app_openapi_schema():
    """Verifica que el esquema OpenAPI está disponible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
