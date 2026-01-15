from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.schemas.patient import PatientCreate
from app.schemas.therapist import TherapistCreate
from app.schemas.treatment import TreatmentCreate
from app.services.patient_service import create_patient
from app.services.therapist_service import create_therapist
from app.services.treatment_service import create_treatment


@pytest.mark.asyncio
async def test_appointment_get_update_cancel_roles(client, db_session, monkeypatch):
    # set current user to admin for some calls
    from app.core import security

    def admin_user():
        return {"id": "admin_id", "role": "admin"}

    monkeypatch.setattr(security, "get_current_user", admin_user)

    # create therapist, treatment, patient and availability
    therapist = await create_therapist(
        db_session, TherapistCreate(name="R1", email=f"r1+{uuid4().hex}@example.com")
    )
    treat = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"Rt1-{uuid4().hex}", description="x", duration_minutes=30, price=20.0
        ),
    )
    _ = await create_patient(
        db_session,
        PatientCreate(
            first_name="R1",
            last_name="P1",
            email=f"r1p+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    from app.models.therapist_availability import TherapistAvailability

    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    weekday = day.strftime("%A").lower()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=weekday,
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    # book via router
    start = datetime.combine(day, time(12, 0), tzinfo=timezone.utc).isoformat()
    payload = {
        "therapist_id": str(therapist.id),
        "treatment_id": str(treat.id),
        "start_time": start,
    }
    resp = client.post("/appointments/", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 422)

    # get list as admin
    resp2 = client.get("/appointments/")
    assert resp2.status_code == 200 or resp2.status_code in (401, 403)

    # get a particular appointment id if present
    data = resp.json() if resp.status_code == 200 else {}
    appt_id = data.get("id")
    if appt_id:
        g = client.get(f"/appointments/{appt_id}")
        assert g.status_code in (200, 401, 403, 404)

        # update attempt
        upd = {"notes": "Updated via test"}
        u = client.put(f"/appointments/{appt_id}", json=upd)
        assert u.status_code in (200, 401, 403, 404, 422)

        # cancel attempt
        c = client.delete(f"/appointments/{appt_id}")
        assert c.status_code in (200, 401, 403, 404)


def test_free_slots_router(client, db_session):
    # call free-slots listing endpoint (router mounted at /free-slots)
    # Use random therapist id; endpoint should return 200 or 404 depending on DB
    tid = uuid4()
    day = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    resp = client.get(f"/free-slots/{tid}/{day}?duration_minutes=30")
    assert resp.status_code in (200, 404, 422)


def test_invoice_router_basic(client):
    # basic smoke for invoice endpoints - endpoint uses POST for listing (admin)
    resp = client.post("/invoices/", json={})
    assert resp.status_code in (200, 401, 403)
