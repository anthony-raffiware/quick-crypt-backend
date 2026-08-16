from typing import List
from pprint import pprint

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.api.v1.dependencies import DBSessionDep
from app.api.v1.core import WrappedRoute, APIException

router = APIRouter(tags=["root"], route_class=WrappedRoute)


@router.get("/")
async def get_root():
    raise APIException(status_code=404)


class Echo(BaseModel):
    echo: int


@router.get("/test", response_model=Echo)
async def get_test():
    return {"echo": 1}


@router.get("/test_list", response_model=List[Echo])
async def get_test_list():
    return [{"echo": 1}]


@router.get("/error", response_model=Echo)
async def get_test():
    raise Exception("Test Internal Error")
