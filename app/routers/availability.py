from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.schemas.availability import AvailabilityCreate, AvailabilityPublic
from app.services.appointment_service import get_daily_availability
from app.services.availability_service import (
    create_availability,
    delete_availability_slot,
    list_therapist_availability,
)
from app.services.therapist_service import get_therapist

router = APIRouter()


@router.post("", response_model=AvailabilityPublic)
async def create_availability_endpoint(
    data: AvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("therapist")),
):
    return await create_availability(db, user["id"], data)


@router.get("")
async def get_availability(
    date: date, therapist_id: UUID, db: AsyncSession = Depends(get_db)
):
    return await get_daily_availability(db, therapist_id, date)


@router.get("/me", response_model=list[AvailabilityPublic])
async def get_my_availability(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("therapist")),
):
    therapist = await get_therapist(db, user["id"])
    return await list_therapist_availability(db, therapist.id)


@router.get("/{therapist_id}", response_model=list[AvailabilityPublic])
async def get_therapist_availability_public(
    therapist_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),  # any logged-in user can see
):
    return await list_therapist_availability(db, therapist_id)


@router.delete("/{slot_id}")
async def delete_availability_slot_endpoint(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("therapist")),
):
    await delete_availability_slot(db, slot_id)
    return {"detail": "Availability slot deleted"}
