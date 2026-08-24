# Quypter API

Simple web based end-to-end encrypted messaging

## Start API


Copy override.env.example to override.env and edit
credentials

```
cp docker/override.env.example override.env
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

### uv


```
uv sync --frozen --no-dev

uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000
```
