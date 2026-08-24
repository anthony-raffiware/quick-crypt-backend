from functools import wraps
from pprint import pprint
import asyncio
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
from app.db import get_db_session
from fastapi import Depends, HTTPException, Request
from fastapi_responseschema import (
  AbstractResponseSchema,
  SchemaAPIRoute,
)
from fastapi_decorators import depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.schema import ResponseMetadata, Collection
from app.models import Session, Base as ObjectBase


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_client_ip(request: Request) -> str:
    return request.client.host


def inject_request(request: Request) -> Request:
    return request
