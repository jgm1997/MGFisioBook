from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    APPOINTMENT_NOT_FOUND_ERROR,
    NOT_ALLOWED_ERROR,
    UNKNOWN_ROLE_ERROR,
)
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentPublic,
    AppointmentUpdate,
)
from app.services.appointment_service import (
    cancel_appointment,
    create_appointment,
    get_appointment,
    list_all_appointments,
    list_patient_appointments,
    list_therapist_appointments,
    update_appointment,
)
from app.services.patient_service import get_patient
from app.services.therapist_service import get_therapist

router = APIRouter()


@router.post("/", response_model=AppointmentPublic)
async def book_appointment(
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("patient")),
):
    patient = await get_patient(db, user["id"])
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appt = await create_appointment(db, patient.id, data, background_tasks)
    return appt


@router.get("/", response_model=list[AppointmentPublic])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    role = user["role"]

    if role == "admin":
        return await list_all_appointments(db)

    if role == "therapist":
        therapist = await get_therapist(db, user["id"])
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist profile not found")
        return await list_therapist_appointments(db, therapist.id)

    if role == "patient":
        patient = await get_patient(db, user["id"])
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        return await list_patient_appointments(db, patient.id)

    raise HTTPException(status_code=403, detail=UNKNOWN_ROLE_ERROR)


@router.get("/{appointment_id}", response_model=AppointmentPublic)
async def get_appointment_endpoint(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = await get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail=APPOINTMENT_NOT_FOUND_ERROR)

    role = user["role"]

    if role == "admin":
        pass  # Admin has access to all appointments
    elif role == "therapist":
        therapist = await get_therapist(db, user["id"])
        if not therapist or appt.therapist_id != therapist.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)
    elif role == "patient":
        patient = await get_patient(db, user["id"])
        if not patient or appt.patient_id != patient.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)
    else:
        raise HTTPException(status_code=403, detail=UNKNOWN_ROLE_ERROR)

    return appt


@router.put("/{appointment_id}", response_model=AppointmentPublic)
async def update_appointment_endpoint(
    appointment_id: UUID,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = await get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail=APPOINTMENT_NOT_FOUND_ERROR)

    role = user["role"]
    allow_override = role == "admin"

    if role == "patient":
        patient = await get_patient(db, user["id"])
        if not patient or appt.patient_id != patient.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)

    if role == "therapist":
        therapist = await get_therapist(db, user["id"])
        if not therapist or appt.therapist_id != therapist.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)

    appt = await update_appointment(db, appt, data, allow_override=allow_override)
    return appt


@router.delete("/{appointment_id}", response_model=AppointmentPublic)
async def cancel_appointment_endpoint(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = await get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    role = user["role"]

    if role == "admin":
        return await cancel_appointment(db, appt)

    if role == "patient":
        patient = await get_patient(db, user["id"])
        if not patient or appt.patient_id != patient.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)
        return await cancel_appointment(db, appt)

    if role == "therapist":
        therapist = await get_therapist(db, user["id"])
        if not therapist or appt.therapist_id != therapist.id:
            raise HTTPException(status_code=403, detail=NOT_ALLOWED_ERROR)
        return await cancel_appointment(db, appt)

    raise HTTPException(status_code=403, detail=UNKNOWN_ROLE_ERROR)
