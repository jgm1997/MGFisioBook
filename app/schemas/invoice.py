from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InvoiceBase(BaseModel):
    appointment_id: UUID
    amount: float
    paid: bool = False


class InvoiceCreate(InvoiceBase):
    pass


class InvoicePublic(InvoiceBase):
    id: UUID
    created_at: datetime
    model_config = {"from_attributes": True}
