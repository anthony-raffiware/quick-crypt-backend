# docker build  -t qc-api:v001 -f docker/Dockerfile .
# Builder Stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies (if required for packages like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY   ./pyproject.toml ./uv.lock ./

RUN useradd -m -d /app --shell /bin/bash app && chown -R app:app /app

USER app

RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

# Runtime Stage
FROM python:3.13-slim AS runtime


ENV database_settings__host=qc_db
ENV database_settings__port=5432
ENV database_settings__database=qc_db
ENV database_settings__pg_schema=qc
ENV database_settings__user=qc_db_user
ENV database_settings__password=ChangeMe12

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /bin /bin

#RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
RUN useradd -m -d /app --shell /bin/bash app && chown -R app:app /app

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1


COPY docker/entry_point.sh /entry_point.sh
RUN chmod +x /entry_point.sh

USER app

EXPOSE 8000
ENTRYPOINT ["/entry_point.sh"]
CMD ["uv", "run", "uvicorn", "app.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]
