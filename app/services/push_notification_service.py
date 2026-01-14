from firebase_admin import messaging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_token import DeviceToken


async def send_push_to_user(db: AsyncSession, user_id: str, title: str, body: str):
    query = select(DeviceToken).where(DeviceToken.user_id == user_id)
    result = await db.execute(query)
    tokens = [row.token for row in result.scalars().all()]
    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body), tokens=tokens
    )

    messaging.send_each_for_multicast(message)
