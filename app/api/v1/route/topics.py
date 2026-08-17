from typing import List, Annotated
from pprint import pprint
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Body, Query, status
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
from app.crud.topics import  load_topic, add_topic_reply
from app.utils import UUID4_PATTERN


router = APIRouter(prefix="/topic", tags=["topics"], route_class=WrappedRoute)


@router.post(
    "/{topic_id}/send_reply",
    response_model=TopicReply,
    status_code=status.HTTP_201_CREATED
)
async def send_topic_reply(
    topic_id: Annotated[str, Path(title="topic id", pattern=UUID4_PATTERN)],
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
    db_session: DBSessionDep
):

    new_reply.topic_id = UUID(topic_id)

    return await add_topic_reply(db_session, new_reply)
