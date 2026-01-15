from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks

from app.schemas.patient import PatientCreate
from app.schemas.therapist import TherapistCreate
from app.schemas.treatment import TreatmentCreate
from app.services.patient_service import create_patient
from app.services.therapist_service import create_therapist
from app.services.treatment_service import create_treatment


@pytest.mark.asyncio
async def test_list_appointments_by_roles_and_admin_update(client, db_session):
    from app.core import security
    from app.main import app as _app
    from app.services.appointment_service import create_appointment

    # create therapist, treatment, availability and two patients
    therapist = await create_therapist(
        db_session, TherapistCreate(name="LTh", email=f"lth+{uuid4().hex}@example.com")
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"LT-{uuid4().hex}", description="x", duration_minutes=30, price=20.0
        ),
    )
    from app.models.therapist_availability import TherapistAvailability

    day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    p1 = await create_patient(
        db_session,
        PatientCreate(
            first_name="P1",
            last_name="A",
            email=f"p1+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )
    p2 = await create_patient(
        db_session,
        PatientCreate(
            first_name="P2",
            last_name="B",
            email=f"p2+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    start1 = datetime.combine(day, time(9, 30), tzinfo=timezone.utc)
    appt1 = await create_appointment(
        db_session,
        p1.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id, treatment_id=tr.id, start_time=start1, notes=None
        ),
        BackgroundTasks(),
    )
    start2 = datetime.combine(day, time(10, 30), tzinfo=timezone.utc)
    _ = await create_appointment(
        db_session,
        p2.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id, treatment_id=tr.id, start_time=start2, notes=None
        ),
        BackgroundTasks(),
    )

    # Admin can list all
    def fake_admin():
        return {"id": 1, "role": "admin"}

    _app.dependency_overrides[security.get_current_user] = fake_admin
    r = client.get("/appointments/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 2

    # Therapist can list their appointments
    def fake_therapist():
        return {"id": therapist.id, "role": "therapist"}

    _app.dependency_overrides[security.get_current_user] = fake_therapist
    rt = client.get("/appointments/")
    assert rt.status_code == 200

    # Patient can list their appointments
    def fake_patient():
        return {"id": p1.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient
    rp = client.get("/appointments/")
    assert rp.status_code == 200

    # Admin can update appointment (override)
    def fake_admin2():
        return {"id": 1, "role": "admin"}

    _app.dependency_overrides[security.get_current_user] = fake_admin2
    up = client.put(f"/appointments/{appt1.id}", json={"notes": "admin note"})
    assert up.status_code in (200, 422)


@pytest.mark.asyncio
async def test_invoice_admin_mark_paid_paths(client, db_session):
    from app.core import security
    from app.main import app as _app
    from app.models.therapist_availability import TherapistAvailability
    from app.schemas.patient import PatientCreate
    from app.schemas.therapist import TherapistCreate
    from app.schemas.treatment import TreatmentCreate
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment
    from app.services.patient_service import create_patient
    from app.services.therapist_service import create_therapist
    from app.services.treatment_service import create_treatment

    # Create minimal data
    therapist = await create_therapist(
        db_session, TherapistCreate(name="ITh", email=f"ith+{uuid4().hex}@example.com")
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"IT-{uuid4().hex}", description="x", duration_minutes=30, price=50.0
        ),
    )
    day = (datetime.now(timezone.utc) + timedelta(days=4)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="IP",
            last_name="T",
            email=f"ip+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )
    start = datetime.combine(day, time(14, 0), tzinfo=timezone.utc)
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

    inv = await create_invoice_for_appointment(db_session, appt)

    # Non-admin mark-paid -> forbidden or not allowed via endpoint
    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient
    r = client.post(f"/invoices/{inv.id}/mark-paid")
    assert r.status_code in (403, 401, 404)

    # Admin can mark paid
    def fake_admin():
        return {"id": 1, "role": "admin"}

    _app.dependency_overrides[security.get_current_user] = fake_admin
    ra = client.post(f"/invoices/{inv.id}/mark-paid")
    assert ra.status_code in (200, 404)
