from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    supabase_user_id: str


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None


class PatientPublic(PatientBase):
    id: UUID

    class Config:
        from_attributes = True
