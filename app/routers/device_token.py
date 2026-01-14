from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.device_token import DeviceToken

router = APIRouter()


@router.post("/")
async def register_device_token(
    token: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    query = select(DeviceToken).where(DeviceToken.token == token)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        return {"status": "already registered"}

    device_token = DeviceToken(token=token, user_id=user["id"])
    db.add(device_token)
    await db.commit()
    return {"status": "registered"}
