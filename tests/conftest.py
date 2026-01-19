import asyncio
import os
import sys
from pathlib import Path

# CRÍTICO: Establecer variables de entorno ANTES de cualquier importación de la app
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use a file-based SQLite DB for tests
TEST_DB_PATH = ROOT / "tests" / "test_db.sqlite"
DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Establecer TODAS las variables de entorno necesarias ANTES de importar la app
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_PUBLISHABLE_KEY"] = "pubkey"
os.environ["SUPABASE_SECRET_KEY"] = "secretkey"
os.environ["SMTP_USER"] = "test@example.com"
os.environ["SMTP_PASSWORD"] = "password"
os.environ["SMTP_HOST"] = "smtp.gmail.com"
os.environ["SMTP_PORT"] = "587"
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ["TEST_DATABASE_URL"] = DATABASE_URL

# AHORA sí importar después de configurar las variables de entorno
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402


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
