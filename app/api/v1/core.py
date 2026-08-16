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
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi_responseschema import (
    AbstractResponseSchema,
    SchemaAPIRoute,
)
from fastapi_decorators import depends
from fastapi.openapi.utils import get_openapi

from app.api.v1.dependencies import inject_request
from app.schema import ResponseMetadata, Collection, APIResponse
from app.models import Base as ObjectBase
from app.utils import generate_uuid_id
from app.db    import sessionmanager

class APIException(HTTPException):
    pass


T = TypeVar("T")


class ResponseSchema(AbstractResponseSchema[T], Generic[T]):
    data: T
    meta: ResponseMetadata

    @classmethod
    def from_exception(cls, reason, status_code, request, **others):

        meta = ResponseMetadata(
            error=status_code >= 400,
            request_id=request.state.request_id,
            data_type='Error'
        )

        return cls(data=reason, meta=meta)

    @classmethod
    def from_api_route(
        cls,
        content: Any,
        status_code: int,
        **others
    ):

        meta = ResponseMetadata(
            error=status_code >= 400,
            request_id=others.get('request_id'),
            data_type=others.get('data_type')
        )

        return cls(data=content, meta=meta)


class WrappedRoute(SchemaAPIRoute):

    response_schema = ResponseSchema

    def _create_endpoint_handler_decorator(
        self,
        wrapper_model: Type[AbstractResponseSchema],
        response_model: Type[Any],
        **params: Any
    ) -> Callable:
        def decorator(func: Callable) -> Callable:

            if asyncio.iscoroutinefunction(func):

                @depends(request=Depends(inject_request))
                @wraps(func)
                async def wrapper(*args: Any, request, **kwargs: Any) -> Any:

                    endpoint_output = await func(*args, **kwargs)

                    if isinstance(endpoint_output, Collection):
                        data_type = 'Collection'
                    elif isinstance(endpoint_output, ObjectBase):
                        data_type = 'Object'
                    else:
                        data_type = 'Data'

                    return self._wrap_endpoint_output(
                        endpoint_output=endpoint_output,
                        wrapper_model=wrapper_model,
                        response_model=response_model,
                        request_id=request.state.request_id,
                        data_type=data_type,
                        **params,
                    )

            else:

                @depends(request=Depends(inject_request))
                @wraps(func)
                def wrapper(*args: Any, request, **kwargs: Any) -> Any:

                    endpoint_output = func(*args, **kwargs)

                    return self._wrap_endpoint_output(
                        endpoint_output=endpoint_output,
                        response_model=response_model,
                        wrapper_model=wrapper_model,
                        request_id=request.state.request_id,
                        **params,
                    )

            return wrapper

        return decorator


async def lifespan(app: FastAPI):

    yield

    if sessionmanager._engine is not None:

        await sessionmanager.close()


async def setup_request(request: Request, call_next):

    request.state.request_id = generate_uuid_id()
    response = await call_next(request)

    return response


def custom_openapi(app):

    def custom_builder():

        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="QuickCrypt API",
            version="1.0.0",
            routes=app.routes
        )
        # Replace the default 422 schema with your custom model
        openapi_schema["components"]["schemas"]["ErrorResponse"] = APIResponse.schema()
        for path in openapi_schema["paths"].values():
            for method in path.values():
                if "422" in method.get("responses", {}):
                    method["responses"]["422"]["content"]["application/json"]["schema"] = {
                        "$ref": "#/components/schemas/ErrorResponse"
                        #"$ref": "#/components/schemas/APIResponse"
                    }

        app.openapi_schema = openapi_schema

        return app.openapi_schema

    return custom_builder
