"""Tests para el servicio de pacientes."""

import pytest

from app.schemas.patient import PatientCreate
from app.services.patient_service import create_patient, get_patient, list_patients


@pytest.mark.asyncio
async def test_create_and_get_patient(db_session):
    """Test crear y obtener un paciente."""
    from uuid import uuid4

    data = PatientCreate(
        first_name="John",
        last_name="Doe",
        email=f"john+{uuid4().hex}@example.com",
        supabase_user_id=uuid4(),
    )

    patient = await create_patient(db_session, data)
    assert patient.id is not None
    assert patient.email == data.email
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"

    fetched = await get_patient(db_session, patient.id)
    assert fetched is not None
    assert fetched.email == data.email
    assert fetched.id == patient.id


@pytest.mark.asyncio
async def test_list_patients(db_session):
    """Test listar pacientes."""
    from uuid import uuid4

    # Crear algunos pacientes para el test
    for i in range(2):
        await create_patient(
            db_session,
            PatientCreate(
                first_name=f"Patient{i}",
                last_name="Test",
                email=f"patient{i}+{uuid4().hex}@example.com",
                supabase_user_id=uuid4(),
            ),
        )

    patients = await list_patients(db_session)
    assert isinstance(patients, list)
    assert len(patients) >= 2
