from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.models.patient import Patient
from app.models.promote_user import PromoteUserRequest
from app.models.therapist import Therapist
from app.services.user_service import update_role

router = APIRouter()


@router.put("/promote-user/{user_id}")
async def promote_user(
    user_id: UUID,
    data: PromoteUserRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    query = select(Patient).where(Patient.supabase_user_id == user_id)
    result = await db.execute(query)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Capture patient data before deletion so we can create the therapist
    first_name = patient.first_name
    last_name = patient.last_name
    phone = patient.phone
    email = patient.email
    supabase_user_id = patient.supabase_user_id

    # Attempt to create or update therapist and delete patient in one transaction
    try:
        # If a therapist already exists for this supabase user, nothing to do
        query = select(Therapist).where(Therapist.supabase_user_id == supabase_user_id)
        result = await db.execute(query)
        existing_by_id = result.scalar_one_or_none()
        if existing_by_id:
            # Remove patient record and commit
            await db.delete(patient)
            await db.commit()
            return {"detail": f"User already promoted as {existing_by_id.name}."}

        # If a therapist exists with the same email, update that record
        query = select(Therapist).where(Therapist.email == email)
        result = await db.execute(query)
        existing_by_email = result.scalar_one_or_none()
        if existing_by_email:
            existing_by_email.name = f"{first_name} {last_name}"
            existing_by_email.phone = phone
            # set supabase_user_id if not already set
            existing_by_email.supabase_user_id = supabase_user_id
            if not existing_by_email.specialty:
                existing_by_email.specialty = "Admin"
            db.add(existing_by_email)
            # delete patient and commit all changes together
            await db.delete(patient)
            await db.commit()
            await db.refresh(existing_by_email)
            await update_role(user_id, data.role)
            return {
                "detail": f"User {existing_by_email.name} promoted to {data.role} successfully."
            }

        # Otherwise create a new therapist
        new_therapist = Therapist(
            name=f"{first_name} {last_name}",
            specialty="Admin",
            phone=phone,
            email=email,
            supabase_user_id=supabase_user_id,
        )
        db.add(new_therapist)
        # delete patient and commit both insert and delete together
        await db.delete(patient)
        await db.commit()
        await db.refresh(new_therapist)

        # Update role in Supabase after database transaction succeeds
        await update_role(user_id, data.role)
        return {
            "detail": f"User {new_therapist.name} promoted to {data.role} successfully."
        }
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Database integrity error: {e.orig}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
