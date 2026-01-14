from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientPublic, PatientUpdate


async def create_patient(db: AsyncSession, data: PatientCreate):
    patient = Patient(**data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient(db: AsyncSession, id: UUID):
    result = await db.execute(select(Patient).where(Patient.id == id))
    return result.scalar_one_or_none()


async def list_patients(db: AsyncSession):
    result = await db.execute(select(Patient))
    return result.scalars().all()


async def update_patient(db: AsyncSession, patient: PatientPublic, data: PatientUpdate):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(patient, k, v)
    await db.commit()
    await db.refresh(patient)
    return patient
