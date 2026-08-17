# QuickCrypt

Web based end-to-end encrypted messaging



```bash
uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000
```

```bash
docker compose -f docker/docker-compose.yml up -d qc_db
docker compose -f docker/docker-compose.yml up -d qc_api
```
