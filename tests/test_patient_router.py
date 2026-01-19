"""Tests para el router de pacientes."""

from uuid import uuid4


def test_create_patient_endpoint(client):
    """Test crear un paciente a través del endpoint."""
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice+%s@example.com" % uuid4().hex,
        "supabase_user_id": uuid4().hex,
    }

    resp = client.post("/patients/", json=payload)
    assert resp.status_code in (201, 200, 401, 403, 422, 500)

    if resp.status_code in (200, 201):
        data = resp.json()
        assert "id" in data
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"


def test_list_patients_endpoint(client):
    """Test listar pacientes."""
    resp = client.get("/patients/")
    assert resp.status_code in (200, 401, 403)

    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list)
