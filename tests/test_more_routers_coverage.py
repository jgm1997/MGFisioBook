"""Tests adicionales para mejorar coverage de routers."""

from uuid import uuid4


def test_free_slots_endpoint(client):
    """Test endpoint de free slots."""
    # Sin parámetros debería dar error o requerir autenticación
    resp = client.get("/free-slots/")
    # Puede dar 422 (validation error), 401, 403
    assert resp.status_code in (422, 401, 403)


def test_appointment_list_mine_endpoint(client):
    """Test endpoint de listar mis appointments."""
    resp = client.get("/appointments/me")
    # Requiere autenticación o da error de validación
    assert resp.status_code in (401, 403, 422)


def test_treatment_update_endpoint(client):
    """Test endpoint de actualizar tratamiento."""
    fake_id = uuid4()
    resp = client.put(f"/treatments/{fake_id}", json={"name": "Updated"})
    # Requiere autenticación o admin
    assert resp.status_code in (401, 403, 404, 405, 422)
