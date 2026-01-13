from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class TherapistBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    active: Optional[bool] = True


class TherapistCreate(TherapistBase):
    pass


class TherapistUpdate(TherapistBase):
    name: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    active: Optional[bool] = True


class TherapistPublic(TherapistBase):
    id: UUID

    class Config:
        from_attributes = True
