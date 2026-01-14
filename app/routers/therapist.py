from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.therapist import TherapistCreate, TherapistPublic
from app.services.therapist_service import (create_therapist, get_therapist,
                                            list_therapists)

router = APIRouter()


@router.post("/", response_model=TherapistPublic)
async def create_therapist_endpoint(
    data: TherapistCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin")),
):
    return await create_therapist(db, data)


@router.get("/", response_model=list[TherapistPublic])
async def list_therapists_endpoint(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin")),
):
    return await list_therapists(db)


@router.get("/{id}", response_model=TherapistPublic)
async def get_therapist_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "therapist")),
):
    therapist = await get_therapist(db, id)
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    return therapist
