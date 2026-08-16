from typing import List, Annotated, Generic, TypeVar, Optional
import base64
from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer


T = TypeVar('T')


class ResponseMetadata(BaseModel):
    error: bool
    request_id: str = '00000'
    data_type: str  = 'Data'


class APIResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMetadata


class CollectionResponseModel(BaseModel, Generic[T]):
    collection: List[T]
    count: int
    page: int
    limit: int


class Collection(dict, Generic[T]):
    collection: List[T]
    count: int
    page: int
    limit: int


class SerializedBinaryData():

    data: bytes

    @field_validator('data', mode='before')
    @classmethod
    def decode_base64_content(cls, value):
        """Accept base64 encoded strings from JSON input"""
        if isinstance(value, str):
            try:
                padded_string = value + '=' * (-len(value) % 4)

                return base64.urlsafe_b64decode(padded_string)
            except Exception as exc:
                raise ValueError('Invalid base64 content')

        return value

    @field_serializer('data')
    def serialize_content(self, value: bytes) -> str:

        if value is None:
            return
        """Serialize bytes as base64 string for JSON output"""
        return base64.urlsafe_b64encode(value).decode('utf-8').rstrip('=')
