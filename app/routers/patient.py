from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.schemas.patient import PatientCreate, PatientPublic
from app.services.patient_service import create_patient, get_patient, list_patients

router = APIRouter()


@router.post("/", response_model=PatientPublic)
async def create_patient_endpoint(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin")),
):
    return await create_patient(db, data)


@router.get("/", response_model=list[PatientPublic])
async def list_patients_endpoint(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin")),
):
    return await list_patients(db)


@router.get("/{id}", response_model=PatientPublic)
async def get_patient_endpoint(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "therapist")),
):
    patient = await get_patient(db, id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
