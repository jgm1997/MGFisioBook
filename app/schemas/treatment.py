from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TreatmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: float


class TreatmentCreate(TreatmentBase):
    pass


class TreatmentUpdate(TreatmentBase):
    name: Optional[str]
    description: Optional[str]
    duration_minutes: Optional[int]
    price: Optional[float]


class TreatmentPublic(TreatmentBase):
    id: UUID
    model_config = {"from_attributes": True}
