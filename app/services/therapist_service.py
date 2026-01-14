from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.therapist import Therapist
from app.schemas.therapist import TherapistCreate


async def create_therapist(db: AsyncSession, data: TherapistCreate):
    therapist = Therapist(**data.model_dump())
    db.add(therapist)
    await db.commit()
    await db.refresh(therapist)
    return therapist


async def get_therapist(db: AsyncSession, id: UUID):
    result = await db.execute(select(Therapist).where(Therapist.id == id))
    return result.scalar_one_or_none()


async def list_therapists(db: AsyncSession):
    result = await db.execute(select(Therapist))
    return result.scalars().all()


async def update_therapist(
    db: AsyncSession, therapist: Therapist, data: TherapistCreate
):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(therapist, k, v)
    await db.commit()
    await db.refresh(therapist)
    return therapist
