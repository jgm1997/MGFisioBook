"""Tests para el router de device tokens."""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_register_device_token_service(db_session):
    """Test registrar token de dispositivo."""
    from app.routers.device_token import register_device_token

    token = uuid4().hex
    user = {"id": uuid4().hex}

    result = await register_device_token(token, db_session, user)

    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] in ("registered", "already registered")


@pytest.mark.asyncio
async def test_register_same_token_twice(db_session):
    """Test registrar el mismo token dos veces."""
    from app.routers.device_token import register_device_token

    token = uuid4().hex
    user_id = uuid4().hex
    user = {"id": user_id}

    # Primera vez
    result1 = await register_device_token(token, db_session, user)
    assert result1["status"] == "registered"

    # Segunda vez - mismo token
    result2 = await register_device_token(token, db_session, user)
    assert result2["status"] == "already registered"
