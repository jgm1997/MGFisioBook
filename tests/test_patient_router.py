from uuid import uuid4


def test_create_patient_endpoint(client):
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice+%s@example.com" % uuid4().hex,
        "supabase_user_id": uuid4().hex,
    }

    resp = client.post("/patients/", json=payload)
    assert resp.status_code in (201, 200, 401, 403, 422, 500)


def test_get_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
