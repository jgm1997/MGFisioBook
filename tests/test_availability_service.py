from datetime import time
from uuid import uuid4

import pytest

from app.schemas.availability import AvailabilityCreate
from app.schemas.therapist import TherapistCreate
from app.services.availability_service import (
    create_availability,
    list_therapist_availability,
)
from app.services.therapist_service import create_therapist


@pytest.mark.asyncio
async def test_create_and_list_availability(db_session):
    therapist = await create_therapist(
        db_session, TherapistCreate(name="AvTh", email=f"av+{uuid4().hex}@example.com")
    )

    data = AvailabilityCreate(
        weekday="Monday", start_time=time(9, 0), end_time=time(12, 0)
    )
    av = await create_availability(db_session, therapist.id, data)
    assert av.id is not None
    assert av.weekday == "monday"

    lst = await list_therapist_availability(db_session, therapist.id)
    assert any(x.id == av.id for x in lst)
