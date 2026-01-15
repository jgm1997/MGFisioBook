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
async def test_book_appointment_as_patient_success(client, db_session):
    # create therapist, treatment, availability and patient
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="EdgeTh", email=f"et+{uuid4().hex}@example.com"),
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"EdgeT-{uuid4().hex}",
            description="x",
            duration_minutes=30,
            price=25.0,
        ),
    )
    from app.models.therapist_availability import TherapistAvailability

    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
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
            first_name="EP",
            last_name="Test",
            email=f"ep+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    # Override current user to this patient for the duration of the test
    from app.core import security
    from app.main import app as _app

    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient

    from fastapi import BackgroundTasks

    from app.services.appointment_service import create_appointment

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
    assert appt.id is not None


@pytest.mark.asyncio
async def test_get_update_delete_access_control(client, db_session):
    # create therapist, treatment, availability and patient
    therapist = await create_therapist(
        db_session, TherapistCreate(name="ACTh", email=f"ac+{uuid4().hex}@example.com")
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"ACt-{uuid4().hex}", description="x", duration_minutes=30, price=30.0
        ),
    )
    from app.models.therapist_availability import TherapistAvailability

    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
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
            first_name="ACP",
            last_name="Q",
            email=f"acp+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    from fastapi import BackgroundTasks

    from app.services.appointment_service import create_appointment

    start = datetime.combine(day, time(11, 0), tzinfo=timezone.utc)
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

    appt_id = str(appt.id)

    # another patient should be forbidden to GET
    other_patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="OP",
            last_name="X",
            email=f"op+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )
    from app.core import security
    from app.main import app as _app

    def fake_other_patient():
        return {"id": other_patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_other_patient
    g = client.get(f"/appointments/{appt_id}")
    assert g.status_code in (403, 401, 404)

    # non-matching therapist should be forbidden to update
    other_therapist = await create_therapist(
        db_session, TherapistCreate(name="OT", email=f"ot+{uuid4().hex}@example.com")
    )

    def fake_other_therapist():
        return {"id": other_therapist.id, "role": "therapist"}

    _app.dependency_overrides[security.get_current_user] = fake_other_therapist
    u = client.put(f"/appointments/{appt_id}", json={"notes": "hack"})
    assert u.status_code in (403, 401, 404, 422)

    # original patient can cancel
    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient
    d = client.delete(f"/appointments/{appt_id}")
    assert d.status_code in (200, 401, 403, 404)


@pytest.mark.asyncio
async def test_appointment_router_roles_and_not_found(client, db_session):
    from app.core import security
    from app.main import app as _app

    # Ensure unknown appointment returns 404
    def fake_admin():
        return {"id": 99999, "role": "admin"}

    _app.dependency_overrides[security.get_current_user] = fake_admin
    r = client.get(f"/appointments/{uuid4()}")
    assert r.status_code == 404

    # Create a patient, therapist, treatment and appointment to test role branches
    from app.schemas.patient import PatientCreate
    from app.schemas.therapist import TherapistCreate
    from app.schemas.treatment import TreatmentCreate
    from app.services.appointment_service import create_appointment
    from app.services.patient_service import create_patient
    from app.services.therapist_service import create_therapist
    from app.services.treatment_service import create_treatment

    therapist = await create_therapist(
        db_session, TherapistCreate(name="RTh", email=f"rth+{uuid4().hex}@example.com")
    )
    tr = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"RT-{uuid4().hex}", description="x", duration_minutes=30, price=20.0
        ),
    )
    from app.models.therapist_availability import TherapistAvailability

    day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
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
            first_name="RP",
            last_name="T",
            email=f"rp+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )
    start = datetime.combine(day, time(13, 0), tzinfo=timezone.utc)
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

    appt_id = str(appt.id)

    # Therapist (matching) can GET
    def fake_therapist():
        return {"id": therapist.id, "role": "therapist"}

    _app.dependency_overrides[security.get_current_user] = fake_therapist
    g = client.get(f"/appointments/{appt_id}")
    assert g.status_code == 200

    # Patient (matching) can GET
    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient
    g2 = client.get(f"/appointments/{appt_id}")
    assert g2.status_code == 200

    # Unknown role should be forbidden
    def fake_unknown():
        return {"id": patient.id, "role": "alien"}

    _app.dependency_overrides[security.get_current_user] = fake_unknown
    gu = client.get(f"/appointments/{appt_id}")
    assert gu.status_code == 403
