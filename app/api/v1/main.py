"""
uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000  --reload
"""
import logging
import uvicorn
from uvicorn.config import LOGGING_CONFIG
from fastapi import FastAPI
from fastapi_responseschema import  wrap_app_responses
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings

from .core import (
    lifespan,
    WrappedRoute,
    setup_request,
    catch_all_exceptions,
    custom_openapi
)
from .route import root_router, session_router, topic_router


APISettings = Settings().api_settings

app = FastAPI(
    lifespan=lifespan,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.openapi = custom_openapi(app)

wrap_app_responses(app, route_class=WrappedRoute)

app.include_router(root_router)
app.include_router(session_router)
app.include_router(topic_router)

app.middleware("http")(setup_request)
app.middleware("http")(catch_all_exceptions)

app.add_middleware(
    CORSMiddleware,
    allow_origins=APISettings.cores.allow_origins,
    allow_credentials=APISettings.cores.allow_credentials,
    allow_methods=['*'],
    allow_headers=['*']
)

LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(levelname)s] %(message)s"
LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"


if __name__ == "__main__":
    uvicorn.run(app, log_config=LOGGING_CONFIG)
