import logging
from typing import List, Annotated, Any
from pprint import pprint
from uuid import UUID
from functools import wraps

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Path,
    Body,
    Query,
    status,
    Depends
)
from fastapi_decorators import depends

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import DBSessionDep
from app.api.v1.core import WrappedRoute
from app.schema.topic import (
    Topic,
    TopicFull,
    NewTopicReply,
    TopicReply
)
from app.schema import Collection, CollectionResponseModel
from app.crud.topics import load_topic, add_topic_reply
from app.crud.session import get_session_key
from app.utils import UUID4_PATTERN, check_param
from app.api.v1.dependencies import inject_request
from app.api.v1.core import verify_session, APIException


router = APIRouter(prefix="/topic", tags=["topics"], route_class=WrappedRoute)
logger = logging.getLogger("quypter-api")


@router.post(
    "/{topic_id}/send_reply/{session_id}",
    response_model=TopicReply,
    status_code=status.HTTP_201_CREATED
)
@verify_session
async def send_topic_reply(
    topic_id: Annotated[str, Path(title="topic id", pattern=UUID4_PATTERN)],
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    new_reply: Annotated[
        NewTopicReply,
        Body(
            title="Submit Reply",
            description="Submit reply",
            examples=[
              {
                "session_key_id": "UUID",
                "topic_reply_pub_key": "BASE64_ED25516_DER",
                "topic_reply_pub_key_sig": "SIGNATURE",
                "data": "ENCRYPTED_DATA"
              }
            ]
        )
    ],
    db_session: DBSessionDep,
):

    session_key_id, session_key  = await get_session_key(db_session, session_id)

    if session_key_id != new_reply.session_key_id:
        raise APIException(status_code=400)

    new_reply.topic_id = UUID(topic_id)

    try:
        return await add_topic_reply(db_session, session_id, new_reply)
    except Exception as e:

        logger.warn(e)
        raise APIException(status_code=400, detail=f"Invalid Topic")


