#!/bin/sh

alembic upgrade head
#
exec uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000
