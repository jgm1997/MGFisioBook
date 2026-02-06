from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.appointment import Appointment
from app.models.therapist_availability import TherapistAvailability
from app.schemas.therapist import TherapistCreate
from app.schemas.treatment import TreatmentCreate, TreatmentUpdate
from app.services.appointment_service import (
    delete_appointment,
    has_conflict,
    is_within_availability,
)
from app.services.invoice_service import (
    create_invoice_for_appointment,
    get_invoice,
    list_invoices,
    list_patient_invoices,
    mark_invoice_paid,
)
from app.services.therapist_service import create_therapist, get_therapist
from app.services.treatment_service import (
    create_treatment,
    get_treatment,
    list_treatments,
    update_treatment,
)


@pytest.mark.asyncio
async def test_treatment_crud(db_session):
    from uuid import uuid4

    unique_name = f"Massage-{uuid4().hex}"
    data = TreatmentCreate(
        name=unique_name, description="Relax", duration_minutes=60, price=50.0
    )
    tr = await create_treatment(db_session, data)
    assert tr.id is not None

    fetched = await get_treatment(db_session, tr.id)
    assert fetched.name == unique_name

    all_t = await list_treatments(db_session)
    assert isinstance(all_t, list)

    upd = TreatmentUpdate(
        name=tr.name,
        description="Deep tissue",
        duration_minutes=tr.duration_minutes,
        price=float(tr.price),
    )
    updated = await update_treatment(db_session, tr.id, upd)
    assert updated.description == "Deep tissue"


@pytest.mark.asyncio
async def test_therapist_create_and_get(db_session):
    data = TherapistCreate(name="Dr. Who", supabase_user_id=uuid4())
    t = await create_therapist(db_session, data)
    print("Created Therapist:", t.name)
    assert t.id is not None

    fetched = await get_therapist(db_session, t.supabase_user_id)
    print("Fetched Therapist:", fetched)
    assert fetched.name == "Dr. Who"


@pytest.mark.asyncio
async def test_invoice_flow(db_session):
    # Create treatment
    from uuid import uuid4

    tr_name = f"Test-{uuid4().hex}"
    tr = await create_treatment(
        db_session,
        TreatmentCreate(name=tr_name, description="x", duration_minutes=30, price=30.0),
    )

    # Create a fake appointment object in DB
    appt = Appointment(
        patient_id=uuid4(),
        therapist_id=uuid4(),
        treatment_id=tr.id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)

    inv = await create_invoice_for_appointment(db_session, appt)
    assert inv.amount == tr.price

    fetched = await get_invoice(db_session, inv.id)
    assert fetched.id == inv.id

    all_inv = await list_invoices(db_session)
    assert isinstance(all_inv, list)

    res = await list_patient_invoices(db_session, [appt.id])
    assert isinstance(res, list)

    inv = await mark_invoice_paid(db_session, inv)
    assert inv.paid is True


@pytest.mark.asyncio
async def test_appointment_availability_and_conflict(db_session):
    # Create therapist and availability
    # availability for the day of the appointment
    target_day = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%A").lower()
    therapist = TherapistAvailability(
        therapist_id=uuid4(),
        weekday=target_day,
        start_time=time(0, 0),
        end_time=time(23, 59),
    )
    db_session.add(therapist)
    await db_session.commit()

    # There's no appointment so conflict should be False
    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=30)
    assert (
        await is_within_availability(db_session, therapist.therapist_id, start, end)
        is True
    )
    assert await has_conflict(db_session, therapist.therapist_id, start, end) is False


@pytest.mark.asyncio
async def test_delete_appointment(db_session):
    # create appointment record
    appt = Appointment(
        patient_id=uuid4(),
        therapist_id=uuid4(),
        treatment_id=uuid4(),
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)

    appt = await delete_appointment(db_session, appt)
    assert appt is not None
