import sys
import asyncio
import logging
import time
import uvicorn
import traceback
#import inspect
from datetime import datetime
from functools import wraps
from pprint import pprint
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
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi_responseschema import (
    AbstractResponseSchema,
    SchemaAPIRoute,
)
from fastapi_decorators import depends
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse


from app.api.v1.dependencies import inject_request
from app.schema import ResponseMetadata, Collection, APIResponse
from app.models import Base as ObjectBase
from app.utils import generate_uuid_id, check_param, verify_tokens
from app.db    import sessionmanager
from app.crud.session import get_session_key


logger = logging.getLogger("quick-crypt")

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

                    request_param, param_type = check_param(func, 'request')

                    if request_param:
                        endpoint_output = await func(*args, request=request, **kwargs)
                    else:
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

    logger.info("QC API started")

    yield

    logger.info("QC API shutting down")

    if sessionmanager._engine is not None:

        await sessionmanager.close()


class CustomFormatter(uvicorn.logging.DefaultFormatter):

    def __init__(self, fmt=None, datefmt=None, style="%", use_colors=None):

        if datefmt is None:
            datefmt = "%Y-%m-%dT%H:%M:%S"

        super().__init__(fmt=fmt, datefmt=datefmt, style=style, use_colors=use_colors)

    def formatTime(self, record, datefmt=None):

          dt = datetime.fromtimestamp(record.created).astimezone()
          return dt.isoformat(timespec='milliseconds')


def setup_logging(app: FastAPI):

    uvicorn_loggers = ["uvicorn", "uvicorn.access", "uvicorn.error"]

    for logger_name in uvicorn_loggers:

        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = False


    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        CustomFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(console_handler)

    # File Handler (Optional)
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # ))
    # logger.addHandler(file_handler)


async def setup_request(request: Request, call_next):

    request.state.request_id = generate_uuid_id()
    start_time               = time.time()

    response = await call_next(request)

    log_request(request, response, start_time)

    return response


def log_request(request: Request, response: Response, start_time: str ):

    process_time = time.time() - start_time

    request_id = request.state.request_id
    timestamp  = time.strftime('%d/%b/%Y:%H:%M:%S %z', time.gmtime())
    ip         = request.client.host if request.client else "-"
    method     = request.method
    path       = request.url.path
    status     = response.status_code

    # Log in Apache-like format
    logger.info(f'{request_id} {ip} - - [{timestamp}] "{method} {path}" {status} {process_time:.4f}')

    return response


async def catch_all_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:

        request_id = request.state.request_id
        timestamp  = time.strftime('%d/%b/%Y:%H:%M:%S %z', time.gmtime())
        ip         = request.client.host if request.client else "-"
        method     = request.method
        path       = request.url.path
        status     = 500 #response.status_code

        logger.info(f'{request_id} {ip} - - [{timestamp}] "{method} {path}" {status}')

        error_message = traceback.format_exc()
        logger.error(f'{request_id} {error_message}')

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


def custom_openapi(app):

    def custom_builder():

        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="QuickCrypt API",
            version="1.0.0",
            routes=app.routes
        )

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


def verify_session(func):

    @depends(request=Depends(inject_request))
    @wraps(func)
    async def wrapper(*args, **kwargs):

        request: Request = kwargs.pop('request')
        session_id       = kwargs.get('session_id')
        db_session       = kwargs.get('db_session')
        session_key      = await get_session_key(db_session, session_id)

        if session_key is None:
            raise APIException(status_code=404, detail=f"Session not found")

        all_headers = dict(request.headers)
        req_utc     = all_headers.get('x-qcs-timestamp');
        req_nonce   = all_headers.get('x-qcs-nonce');
        req_sig     = all_headers.get('x-qcs-signature');

        if not req_utc or not req_nonce or not req_sig:
            raise APIException(status_code=401)

        tokens = {
           "sessionUuid": session_id,
           "date": req_utc,
           "nonce": req_nonce
        }

        if not verify_tokens(tokens, req_sig, session_key):
            raise APIException(status_code=401)

        request_param, param_ype = check_param(func, 'request')

        if request_param:
            return await func(*args, request=request, **kwargs)
        else:
            return await func(*args, **kwargs)

    return wrapper

