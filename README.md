# Quypter API

Front-end API for the Quypter Web App


## Running dev instance


Edit database_settings in config.json


```
uv sync --frozen --no-dev

uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000
```


