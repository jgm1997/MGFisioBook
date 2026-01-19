# MGFisioBook

MGFisioBook backend API — appointments, patients, therapists, invoices and notifications.

This repository contains the FastAPI-based backend for MGFisioBook. It provides REST endpoints for managing appointments, therapists, patients, treatments, invoices and device tokens. The project includes email and push notification support and uses SQLAlchemy + Alembic for database migrations.

## Contents

- `app/` — application package with routers, models, schemas and services.
- `migrations/` — Alembic migrations for database schema.
- `tests/` — minimal tests.
- `requirements.txt` / `pyproject.toml` — dependencies.

## Quick Start (development)

1. Create a Python virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure environment variables

Create a `.env` or export the following environment variables as required by `app/core/config.py`:

- `DATABASE_URL` — SQLAlchemy database URL (e.g. `sqlite:///./dev.db` or a Postgres URL)
- `SECRET_KEY` — application secret
- `EMAIL_*` — SMTP settings if sending emails
- `FIREBASE_*` / `SUPABASE_*` — optional integrations

1. Run migrations (if using Postgres or another DB):

```bash
alembic upgrade head
```

1. Start the application:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000` and OpenAPI docs at `http://127.0.0.1:8000/docs`.

## Running tests

Run the included tests with `pytest`:

```bash
pytest -q
```

Testing notes:

- Tests use an async in-memory SQLite database by default. To use a different test database (for example Postgres), set the `TEST_DATABASE_URL` environment variable before running tests, e.g.:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/testdb"
pytest -q
```

- The test suite provides fixtures in `tests/conftest.py` that override the application's `get_db` dependency so tests run against the test database.

Integration testing note:

- Some integration tests hit the running FastAPI app and expect the test database to be accessible from both the test fixtures and the `TestClient`. Using the default in-memory SQLite may cause schema visibility issues across connections. For reliable integration tests, set `TEST_DATABASE_URL` to a file-based SQLite (`sqlite+aiosqlite:////full/path/to/tests/test_db.sqlite`) or a Postgres test database before running tests.

## Database

The project uses SQLAlchemy models in `app/models` and Alembic for migrations. See `alembic.ini` and `migrations/` for migration configuration.

## Email & Notifications

Email templates live in `app/templates/email`. Email sending is implemented in `app/core/email.py` and `app/services/email_notification_service.py`. Push notifications are handled in `app/services/push_notification_service.py` and `app/core/firebase.py` / `app/core/supabase_client.py`.

## Deployment (Docker)

There is a `Dockerfile` and `docker-compose.yml` for containerized deployment. Build and run with:

```bash
docker-compose up --build
```

## Contributing

Contributions are welcome. Open an issue or a pull request with a clear description and tests for changes.
