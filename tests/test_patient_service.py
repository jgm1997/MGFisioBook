import pytest

from app.schemas.patient import PatientCreate
from app.services.patient_service import create_patient, get_patient, list_patients


@pytest.mark.asyncio
async def test_create_and_get_patient(db_session):
    from uuid import uuid4

    data = PatientCreate(
        first_name="John",
        last_name="Doe",
        email=f"john+{uuid4().hex}@example.com",
        supabase_user_id=f"user_{uuid4().hex}",
    )

    patient = await create_patient(db_session, data)
    assert patient.id is not None
    assert patient.email == data.email

    fetched = await get_patient(db_session, patient.id)
    assert fetched is not None
    assert fetched.email == data.email


@pytest.mark.asyncio
async def test_list_patients(db_session):
    # start with clean DB since fixtures create schema per session
    patients = await list_patients(db_session)
    assert isinstance(patients, list)
