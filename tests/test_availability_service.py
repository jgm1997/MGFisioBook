"""Tests para el servicio de disponibilidad de terapeutas."""

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
async def test_create_availability(db_session):
    """Test crear disponibilidad para un terapeuta."""
    therapist = await create_therapist(
        db_session, TherapistCreate(name="AvTh", email=f"av+{uuid4().hex}@example.com")
    )

    data = AvailabilityCreate(
        weekday="Monday", start_time=time(9, 0), end_time=time(12, 0)
    )
    av = await create_availability(db_session, therapist.id, data)

    assert av.id is not None
    assert av.weekday == "monday"
    assert av.start_time == time(9, 0)
    assert av.end_time == time(12, 0)
    assert av.therapist_id == therapist.id


@pytest.mark.asyncio
async def test_list_therapist_availability(db_session):
    """Test listar disponibilidad de un terapeuta."""
    therapist = await create_therapist(
        db_session,
        TherapistCreate(name="ListTh", email=f"lst+{uuid4().hex}@example.com"),
    )

    # Crear múltiples bloques de disponibilidad
    days = [
        ("Monday", time(9, 0), time(13, 0)),
        ("Wednesday", time(14, 0), time(18, 0)),
        ("Friday", time(10, 0), time(16, 0)),
    ]

    created_avs = []
    for weekday, start, end in days:
        data = AvailabilityCreate(weekday=weekday, start_time=start, end_time=end)
        av = await create_availability(db_session, therapist.id, data)
        created_avs.append(av)

    # Listar todas las disponibilidades
    lst = await list_therapist_availability(db_session, therapist.id)
    assert len(lst) >= 3

    # Verificar que todas las creadas están en la lista
    for created in created_avs:
        assert any(x.id == created.id for x in lst)
