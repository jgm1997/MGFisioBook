import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base

# Ensure project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide minimal environment variables required by app.core.config.Settings
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "pubkey")
os.environ.setdefault("SUPABASE_SECRET_KEY", "secretkey")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "password")

# Use a file-based SQLite DB for tests and make sure the app uses it
TEST_DB_PATH = ROOT / "tests" / "test_db.sqlite"
test_db_url = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ.setdefault("TEST_DATABASE_URL", test_db_url)
# Set DATABASE_URL env used by application import
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL"))


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture()
def client(engine, monkeypatch):
    # Override the application's get_db dependency to use the test engine
    async def _get_test_db():
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    from app.core import database

    monkeypatch.setattr(database, "get_db", _get_test_db)

    # Bypass security dependencies for tests by overriding FastAPI dependencies
    from app.core import security

    def _fake_current_user():
        return {"id": "user_test", "email": "test@example.com", "role": "admin"}

    app.dependency_overrides[security.get_current_user] = _fake_current_user

    with TestClient(app) as tc:
        yield tc
