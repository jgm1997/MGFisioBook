from firebase_admin import messaging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import appointment
from app.models.device import Device


async def send_push_to_user(db: AsyncSession, user_id: str, title: str, body: str):
    query = select(Device).where(Device.supabase_user_id == user_id)
    result = await db.execute(query)
    tokens = [row.token for row in result.scalars().all()]
    if not tokens:
        return
    appointment_query = select(appointment.Appointment).where(
        appointment.Appointment.patient_id == user_id
    )
    appointment_result = await db.execute(appointment_query)
    appointment_obj = appointment_result.scalar_one_or_none()
    if not appointment_obj:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
        data={"appointmentId": appointment_obj.ids},
    )

    messaging.send_each_for_multicast(message)
