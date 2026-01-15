from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.schemas.patient import PatientCreate
from app.schemas.therapist import TherapistCreate
from app.schemas.treatment import TreatmentCreate
from app.services.appointment_service import create_appointment, update_appointment
from app.services.free_slot_service import get_free_slots
from app.services.patient_service import create_patient
from app.services.therapist_service import create_therapist
from app.services.treatment_service import create_treatment


@pytest.mark.asyncio
async def test_create_appointment_and_conflicts(db_session):
    # create therapist
    therapist = await create_therapist(
        db_session, TherapistCreate(name="Thera", email=f"t+{uuid4().hex}@example.com")
    )

    # create treatment
    treat_name = f"Ther-{uuid4().hex}"
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=treat_name, description="x", duration_minutes=30, price=30.0
        ),
    )

    # add availability matching tomorrow
    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    weekday = day.strftime("%A").lower()
    from app.models.therapist_availability import TherapistAvailability

    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=weekday,
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    # create patient
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="P",
            last_name="Q",
            email=f"p+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    # create appointment within availability
    start = datetime.combine(day, time(10, 0), tzinfo=timezone.utc)
    data = AppointmentCreate(
        therapist_id=therapist.id,
        treatment_id=treatment.id,
        start_time=start,
        notes=None,
    )

    from fastapi import BackgroundTasks

    appt = await create_appointment(db_session, patient.id, data, BackgroundTasks())
    assert appt.id is not None

    # creating another appointment overlapping should raise
    data2 = AppointmentCreate(
        therapist_id=therapist.id,
        treatment_id=treatment.id,
        start_time=start + timedelta(minutes=15),
        notes=None,
    )
    with pytest.raises(Exception):
        await create_appointment(db_session, patient.id, data2, BackgroundTasks())


@pytest.mark.asyncio
async def test_update_appointment_conflict_and_override(db_session):
    # Setup therapist, treatment, patient and availability
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="Thera2", email=f"t2+{uuid4().hex}@example.com"),
    )
    treat_name = f"Ther2-{uuid4().hex}"
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=treat_name, description="x", duration_minutes=30, price=30.0
        ),
    )
    day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    weekday = day.strftime("%A").lower()
    from app.models.therapist_availability import TherapistAvailability

    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=weekday,
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="P2",
            last_name="Q2",
            email=f"p2+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    start1 = datetime.combine(day, time(11, 0), tzinfo=timezone.utc)
    from fastapi import BackgroundTasks

    _ = await create_appointment(
        db_session,
        patient.id,
        AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start1,
            notes=None,
        ),
        BackgroundTasks(),
    )

    # create second appointment later
    start2 = datetime.combine(day, time(13, 0), tzinfo=timezone.utc)
    appt2 = await create_appointment(
        db_session,
        patient.id,
        AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start2,
            notes=None,
        ),
        BackgroundTasks(),
    )

    # try to move appt2 to overlap appt1
    update = AppointmentUpdate(start_time=start1 + timedelta(minutes=15))
    with pytest.raises(Exception):
        await update_appointment(db_session, appt2, update, allow_override=False)

    # allow override should succeed
    updated = await update_appointment(db_session, appt2, update, allow_override=True)

    # normalize both to UTC-aware datetimes for reliable comparison
    def to_aware(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    assert to_aware(updated.start_time) == to_aware(update.start_time)


@pytest.mark.asyncio
async def test_get_free_slots(db_session):
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="Thera3", email=f"t3+{uuid4().hex}@example.com"),
    )
    day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    weekday = day.strftime("%A").lower()
    from app.models.therapist_availability import TherapistAvailability

    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=weekday,
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    db_session.add(av)
    await db_session.commit()

    # no appointments: expect 2 slots of 30 minutes
    slots = await get_free_slots(db_session, therapist.id, day, 30)
    assert len(slots) >= 2
