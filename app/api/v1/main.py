"""
uv run uvicorn app.api.v1.main:app  --host 0.0.0.0 --port 8000  --reload --root-path /api/v1
"""
import asyncio
import logging
import uvicorn
from pydantic import BaseModel
from typing import (
    Generic,
    Type,
    Callable,
    TypeVar,
    Any,
    Optional,
    List,
    Annotated
)
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi_responseschema import  wrap_app_responses
from fastapi.middleware.cors import CORSMiddleware

from app.schema import ResponseMetadata
from app.config import Settings

from .core import lifespan, WrappedRoute, setup_request, custom_openapi
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
# app.mount("/api", app)

wrap_app_responses(app, route_class=WrappedRoute)
app.include_router(root_router)
app.include_router(session_router)
app.include_router(topic_router)

app.middleware("http")(setup_request)


@app.middleware("http")
async def catch_all_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:

        print(exc)

        meta = ResponseMetadata(
            error=True,
            request_id=request.state.request_id,
            data_type='Error'
        )

        return JSONResponse(
            status_code=500,
            content={
               "data": 'Server Error',
               "meta": meta.model_dump()
            }
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=APISettings.cores.allow_origins,
    allow_credentials=APISettings.cores.allow_credentials,
    allow_methods=['*'],
    allow_headers=['*']
)
