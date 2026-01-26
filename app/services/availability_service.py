from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.therapist_availability import TherapistAvailability
from app.schemas.availability import AvailabilityCreate


async def create_availability(
    db: AsyncSession,
    therapist_id: UUID,
    data: AvailabilityCreate,
) -> TherapistAvailability:
    availability = TherapistAvailability(
        therapist_id=therapist_id,
        weekday=data.weekday.lower(),
        start_time=data.start_time,
        end_time=data.end_time,
    )
    db.add(availability)
    await db.commit()
    await db.refresh(availability)
    return availability


async def list_therapist_availability(
    db: AsyncSession,
    therapist_id: UUID,
) -> list[TherapistAvailability]:
    q = select(TherapistAvailability).where(
        TherapistAvailability.therapist_id == therapist_id
    )
    result = await db.execute(q)
    return result.scalars().all()


async def delete_availability_slot(db: AsyncSession, slot_id: UUID):
    query = delete(TherapistAvailability).where(TherapistAvailability.id == slot_id)
    await db.execute(query)
    await db.commit()
