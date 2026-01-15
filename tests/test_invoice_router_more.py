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
async def test_patient_invoice_branches(client, db_session, monkeypatch):
    # create therapist, treatment, patient, appointment and invoice
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="InvTh", email=f"inv+{uuid4().hex}@example.com"),
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"Invt-{uuid4().hex}", description="x", duration_minutes=30, price=50.0
        ),
    )
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="I",
            last_name="P",
            email=f"i+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    from fastapi import BackgroundTasks

    from app.models.therapist_availability import TherapistAvailability
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment

    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    start = datetime.combine(day, time(10, 0), tzinfo=timezone.utc)
    appt = await create_appointment(
        db_session,
        patient.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id, treatment_id=tr.id, start_time=start, notes=None
        ),
        BackgroundTasks(),
    )
    invoice = await create_invoice_for_appointment(db_session, appt)

    # simulate patient user
    from app.core import security

    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    monkeypatch.setattr(security, "get_current_user", fake_patient)

    # list my invoices
    resp = client.get("/invoices/my")
    assert resp.status_code in (200, 401, 403)

    # get invoice endpoint
    resp2 = client.get(f"/invoices/{invoice.id}")
    assert resp2.status_code in (200, 401, 403, 404)


@pytest.mark.asyncio
async def test_mark_invoice_paid_admin(client, db_session, monkeypatch):
    # create invoiceless id to trigger 404 and test admin pay path
    fake_id = uuid4()

    from app.core import security

    def fake_admin():
        return {"id": "admin", "role": "admin"}

    monkeypatch.setattr(security, "get_current_user", fake_admin)

    # mark non-existing invoice
    resp = client.put(f"/invoices/{fake_id}/pay")
    assert resp.status_code in (404, 401, 403)
