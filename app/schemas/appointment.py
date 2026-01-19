from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AppointmentBase(BaseModel):
    therapist_id: UUID
    treatment_id: UUID
    start_time: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AppointmentPublic(AppointmentBase):
    id: UUID
    patient_id: UUID
    status: str
    model_config = {"from_attributes": True}
