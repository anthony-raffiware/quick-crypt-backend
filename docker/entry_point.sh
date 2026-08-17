#!/bin/sh

alembic upgrade head
#
exec uv run uvicorn app.api.v1.main:app \
        --host 0.0.0.0 \
        --port 8000  \
        --proxy-headers \
        --forwarded-allow-ips="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
