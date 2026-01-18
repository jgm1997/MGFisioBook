import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Therapist(Base):
    __tablename__ = "therapists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True, unique=True)
    active = Column(Boolean, default=True)
    supabase_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
