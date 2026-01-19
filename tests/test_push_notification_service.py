from uuid import uuid4

import pytest

from app.schemas.patient import PatientCreate
from app.services.patient_service import create_patient
from app.services.push_notification_service import send_push_to_user


@pytest.mark.asyncio
async def test_send_push_no_tokens(db_session, monkeypatch):
    # Ensure no tokens -> function returns None and does not call messaging
    called = {"sent": False}

    class FakeMessaging:
        class Notification:
            def __init__(self, title, body):
                self.title = title
                self.body = body

        class MulticastMessage:
            def __init__(self, notification, tokens):
                self.notification = notification
                self.tokens = tokens

        @staticmethod
        def send_each_for_multicast(msg):
            called["sent"] = True

    monkeypatch.setattr(
        "app.services.push_notification_service.messaging", FakeMessaging
    )

    result = await send_push_to_user(db_session, "nonexistent_user", "T", "B")
    assert result is None
    assert called["sent"] is False


@pytest.mark.asyncio
async def test_send_push_with_tokens(db_session, monkeypatch):
    # create a patient to act as user id (supabase id)
    patient = await create_patient(
        db_session,
        PatientCreate(
            first_name="PN",
            last_name="U",
            email=f"p+{uuid4().hex}@example.com",
            supabase_user_id=uuid4(),
        ),
    )

    # insert a device token directly
    from app.models.device_token import DeviceToken

    dt = DeviceToken(user_id=str(patient.supabase_user_id), token=uuid4().hex)
    db_session.add(dt)
    await db_session.commit()

    called = {"sent": False}

    class FakeMessaging:
        class Notification:
            def __init__(self, title, body):
                self.title = title
                self.body = body

        class MulticastMessage:
            def __init__(self, notification, tokens):
                self.notification = notification
                self.tokens = tokens

        @staticmethod
        def send_each_for_multicast(msg):
            called["sent"] = True

    monkeypatch.setattr(
        "app.services.push_notification_service.messaging", FakeMessaging
    )

    await send_push_to_user(db_session, str(patient.supabase_user_id), "Title", "Body")
    assert called["sent"] is True
