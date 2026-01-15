from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.therapist_availability import TherapistAvailability
from app.models.treatment import Treatment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.email_notification_service import send_appointment
from app.services.push_notification_service import send_push_to_user


async def __has_conflict(
    db: AsyncSession, therapist_id: UUID, start: datetime, end: datetime
) -> bool:
    query = select(Appointment).where(
        Appointment.therapist_id == therapist_id,
        Appointment.start_time < end,
        Appointment.end_time > start,
        Appointment.status == AppointmentStatus.scheduled,
    )
    result = await db.execute(query)
    return result.scalars().first() is not None


async def __is_within_availability(
    db: AsyncSession, therapist_id: UUID, start: datetime, end: datetime
) -> bool:
    weekday = start.strftime("%A").lower()

    query = select(TherapistAvailability).where(
        TherapistAvailability.therapist_id == therapist_id,
        TherapistAvailability.weekday == weekday,
        TherapistAvailability.start_time <= start.time(),
        TherapistAvailability.end_time >= end.time(),
    )
    result = await db.execute(query)
    return result.scalars().first() is not None


async def create_appointment(
    db: AsyncSession,
    patient_id: UUID,
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
) -> Appointment:
    query = select(Treatment).where(Treatment.id == data.treatment_id)
    result = await db.execute(query)
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found.")

    start = data.start_time
    end = start + timedelta(minutes=treatment.duration_minutes)

    if not await __is_within_availability(db, data.therapist_id, start, end):
        raise HTTPException(
            status_code=400, detail="Therapist not available at this time."
        )

    if await __has_conflict(db, data.therapist_id, start, end):
        raise HTTPException(
            status_code=400, detail="Appointment conflicts with existing booking."
        )

    appointment = Appointment(
        patient_id=patient_id,
        therapist_id=data.therapist_id,
        treatment_id=data.treatment_id,
        start_time=start,
        end_time=end,
        notes=data.notes,
    )

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    background_tasks.add_task(
        send_appointment,
        "confirmation",
        patient=appointment.patient,
        therapist=appointment.therapist,
        treatment=appointment.treatment,
        appointment=appointment,
    )

    background_tasks.add_task(
        send_push_to_user,
        db,
        appointment.patient_id,
        "Cita confirmada",
        f"Tu cita para {treatment.name} el {start.strftime('%Y-%m-%d %H:%M')} ha sido confirmada.",
    )

    return appointment


async def get_appointment(
    db: AsyncSession, appointment_id: UUID
) -> Optional[Appointment]:
    query = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_all_appointments(db: AsyncSession) -> list[Appointment]:
    query = select(Appointment).order_by(Appointment.start_time.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def list_therapist_appointments(
    db: AsyncSession, therapist_id: UUID
) -> list[Appointment]:
    query = (
        select(Appointment)
        .where(Appointment.therapist_id == therapist_id)
        .order_by(Appointment.start_time.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def list_patient_appointments(
    db: AsyncSession, patient_id: UUID
) -> list[Appointment]:
    query = (
        select(Appointment)
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.start_time.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def update_appointment(
    db: AsyncSession,
    appointment: Appointment,
    data: AppointmentUpdate,
    allow_override: bool = False,
) -> Appointment:
    update_data = data.model_dump(exclude_unset=True)

    new_start = update_data.get("start_time", appointment.start_time)
    new_end = update_data.get("end_time", appointment.end_time)

    if new_start != appointment.start_time or new_end != appointment.end_time:
        if (
            not await __is_within_availability(
                db, appointment.therapist_id, new_start, new_end
            )
            and not allow_override
        ):
            raise HTTPException(
                status_code=400, detail="Therapist not available at this time"
            )

        if (
            await __has_conflict(
                db,
                appointment.therapist_id,
                new_start,
                new_end,
            )
            and not allow_override
        ):
            raise HTTPException(
                status_code=400,
                detail="Appointment conflicts with existing booking",
            )

    for k, v in update_data.items():
        setattr(appointment, k, v)

    await db.commit()
    await db.refresh(appointment)
    return appointment


async def cancel_appointment(db: AsyncSession, appointment: Appointment) -> Appointment:
    appointment.status = AppointmentStatus.cancelled
    await db.commit()
    await db.refresh(appointment)
    return appointment
