import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    notes = Column(Text)
    supabase_user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
