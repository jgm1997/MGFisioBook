import uuid

from sqlalchemy import UUID, Column, String, Text

from app.models.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    notes = Column(Text)
    supabase_user_id = Column(String, nullable=False, unique=True)
