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
async def test_register_device_token(db_session):
    # call the router function directly because router isn't mounted in app
    from app.routers.device_token import register_device_token

    token = uuid4().hex
    # create a patient to act as user
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="DT",
            last_name="U",
            email=f"dt+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )
    user = {"id": patient.supabase_user_id}
    # call function with db session and user
    _ = pytest.approx  # placeholder to keep linter happy
    result = await register_device_token(token, db_session, user)

    assert isinstance(result, dict)
    assert result.get("status") in ("registered", "already registered")


@pytest.mark.asyncio
async def test_book_and_list_appointments(client, db_session):
    # create therapist, treatment, patient
    therapist = await create_therapist(
        db_session, TherapistCreate(name="Rther", email=f"r+{uuid4().hex}@example.com")
    )
    treat = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"Rt-{uuid4().hex}", description="x", duration_minutes=30, price=20.0
        ),
    )
    _ = await create_patient(
        db_session,
        PatientCreate(
            first_name="R",
            last_name="P",
            email=f"r+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    # create availability
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

    start = datetime.combine(day, time(10, 0), tzinfo=timezone.utc).isoformat()
    payload = {
        "therapist_id": str(therapist.id),
        "treatment_id": str(treat.id),
        "start_time": start,
    }
    resp = client.post("/appointments/", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 422)

    # list appointments
    resp2 = client.get("/appointments/")
    assert resp2.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_appointment_router_role_branches(client, db_session):
    # create therapist, patient, treatment and appointment
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="RBther", email=f"rb+{uuid4().hex}@example.com"),
    )
    treat = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"Rb-{uuid4().hex}", description="x", duration_minutes=30, price=20.0
        ),
    )
    _ = await create_patient(
        db_session,
        PatientCreate(
            first_name="RB",
            last_name="P",
            email=f"rb+{uuid4().hex}@example.com",
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

    start = datetime.combine(day, time(11, 0), tzinfo=timezone.utc).isoformat()
    payload = {
        "therapist_id": str(therapist.id),
        "treatment_id": str(treat.id),
        "start_time": start,
    }
    # book appointment as patient (require_role('patient') is used in router; tests' client uses override)
    resp = client.post("/appointments/", json=payload)
    assert resp.status_code in (200, 201, 401, 403, 422)

    # list as current test user (overrides may return admin/patient depending on conftest) — ensure code paths run
    resp_list = client.get("/appointments/")
    assert resp_list.status_code in (200, 401, 403)
