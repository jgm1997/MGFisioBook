#!/usr/bin/env bash
set -e

# This script runs database migrations and starts the app

# Run database migrations then start the app
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
