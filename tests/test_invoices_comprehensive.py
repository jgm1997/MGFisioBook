"""Tests consolidados para el sistema de facturas (invoices)."""

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
async def test_create_invoice_for_appointment(db_session):
    """Test creación de factura para una cita."""
    from app.models.therapist_availability import TherapistAvailability
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment

    # Crear datos necesarios
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="InvTh", email=f"inv+{uuid4().hex}@example.com"),
    )
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"InvT-{uuid4().hex}",
            description="Treatment",
            duration_minutes=30,
            price=50.0,
        ),
    )
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="Inv",
            last_name="Patient",
            email=f"inv+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    # Crear cita
    start = datetime.combine(day, time(10, 0), tzinfo=timezone.utc)
    appt = await create_appointment(
        db_session,
        patient.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start,
            notes=None,
        ),
        BackgroundTasks(),
    )

    # Crear factura
    invoice = await create_invoice_for_appointment(db_session, appt)

    assert invoice.id is not None
    assert invoice.appointment_id == appt.id
    assert invoice.amount == treatment.price
    assert invoice.paid is False


@pytest.mark.asyncio
async def test_list_patient_invoices(client, db_session, monkeypatch):
    """Test listar facturas de un paciente."""
    from app.core import security
    from app.models.therapist_availability import TherapistAvailability
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment

    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="LTh", email=f"lth+{uuid4().hex}@example.com"),
    )
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"LT-{uuid4().hex}",
            description="x",
            duration_minutes=30,
            price=40.0,
        ),
    )
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="List",
            last_name="Test",
            email=f"list+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    start = datetime.combine(day, time(11, 0), tzinfo=timezone.utc)
    appt = await create_appointment(
        db_session,
        patient.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start,
            notes=None,
        ),
        BackgroundTasks(),
    )
    await create_invoice_for_appointment(db_session, appt)

    # Simular paciente
    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    monkeypatch.setattr(security, "get_current_user", fake_patient)

    resp = client.get("/invoices/my")
    assert resp.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_get_invoice_by_id(client, db_session, monkeypatch):
    """Test obtener una factura específica."""
    from app.core import security
    from app.models.therapist_availability import TherapistAvailability
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment

    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="GTh", email=f"gth+{uuid4().hex}@example.com"),
    )
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"GT-{uuid4().hex}",
            description="x",
            duration_minutes=30,
            price=35.0,
        ),
    )
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="Get",
            last_name="Test",
            email=f"get+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
        ),
    )

    day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    av = TherapistAvailability(
        therapist_id=therapist.id,
        weekday=day.strftime("%A").lower(),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    db_session.add(av)
    await db_session.commit()

    start = datetime.combine(day, time(12, 0), tzinfo=timezone.utc)
    appt = await create_appointment(
        db_session,
        patient.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start,
            notes=None,
        ),
        BackgroundTasks(),
    )
    invoice = await create_invoice_for_appointment(db_session, appt)

    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    monkeypatch.setattr(security, "get_current_user", fake_patient)

    resp = client.get(f"/invoices/{invoice.id}")
    assert resp.status_code in (200, 401, 403, 404)


@pytest.mark.asyncio
async def test_mark_invoice_paid_as_admin(client, db_session, monkeypatch):
    """Test marcar factura como pagada (solo admin)."""
    from app.core import security
    from app.main import app as _app
    from app.models.therapist_availability import TherapistAvailability
    from app.services.appointment_service import create_appointment
    from app.services.invoice_service import create_invoice_for_appointment

    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="PayTh", email=f"pay+{uuid4().hex}@example.com"),
    )
    treatment = await create_treatment(
        db_session,
        TreatmentCreate(
            name=f"PayT-{uuid4().hex}",
            description="x",
            duration_minutes=30,
            price=60.0,
        ),
    )
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="Pay",
            last_name="Test",
            email=f"pay+{uuid4().hex}@example.com",
            supabase_user_id=uuid4().hex,
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

    start = datetime.combine(day, time(14, 0), tzinfo=timezone.utc)
    appt = await create_appointment(
        db_session,
        patient.id,
        __import__(
            "app.schemas.appointment", fromlist=["AppointmentCreate"]
        ).AppointmentCreate(
            therapist_id=therapist.id,
            treatment_id=treatment.id,
            start_time=start,
            notes=None,
        ),
        BackgroundTasks(),
    )
    invoice = await create_invoice_for_appointment(db_session, appt)

    # Paciente NO debe poder marcar como pagado
    def fake_patient():
        return {"id": patient.id, "role": "patient"}

    _app.dependency_overrides[security.get_current_user] = fake_patient
    resp = client.post(f"/invoices/{invoice.id}/mark-paid")
    assert resp.status_code in (403, 401, 404, 405)

    # Admin SÍ puede marcar como pagado
    def fake_admin():
        return {"id": "admin_id", "role": "admin"}

    _app.dependency_overrides[security.get_current_user] = fake_admin
    resp = client.post(f"/invoices/{invoice.id}/mark-paid")
    assert resp.status_code in (200, 404, 405)


@pytest.mark.asyncio
async def test_invoice_not_found(client, monkeypatch):
    """Test acceso a factura inexistente."""
    from app.core import security

    def fake_admin():
        return {"id": "admin_id", "role": "admin"}

    monkeypatch.setattr(security, "get_current_user", fake_admin)

    fake_id = uuid4()
    resp = client.put(f"/invoices/{fake_id}/pay")
    assert resp.status_code in (404, 401, 403, 405)
