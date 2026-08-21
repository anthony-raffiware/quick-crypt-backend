import logging
from typing import Annotated
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Body,
    Query,
    Request,
    Response,
    status
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import DBSessionDep
from app.api.v1.core import WrappedRoute
from app.schema import (
    NewSession,
    Session,
    Topic,
    TopicFull,
    NewTopic,
    ReplyComment,
    NewReplyComment,
    Collection,
    CollectionResponseModel
)
from app.crud.session import create_session, load_session
from app.crud.topics import (
    create_topic,
    load_session_topics,
    load_session_topic_replies,
    load_session_replies,
    load_topic_with_replies,
    add_reply_comment
)
from app.utils import UUID4_PATTERN
from app.api.v1.core import verify_session, APIException

router = APIRouter(prefix="/session", tags=["session"], route_class=WrappedRoute)
logger = logging.getLogger("quypter-api")

@router.post("/new",
    response_model=Session,
    status_code=status.HTTP_201_CREATED
)
async def new_session(
    new_session: Annotated[
        NewSession,
        Body(
            title="New Session",
            description="New session data",
            examples=[{"pub_key": "BASE64_ED25516_DER"}]
        )
    ],
    db_session: DBSessionDep
):

    return await create_session(db_session, key=new_session.pub_key )


@router.get("/{session_id}", response_model=Session)
@verify_session
async def get_session(
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    db_session: DBSessionDep
):

    try:
        session = await load_session(db_session, session_id)

        if not session:
            raise ValueError("Session not found")

        return session
    except ValueError:

        raise HTTPException(status_code=404, detail=f"Session not found")


@router.post("/{session_id}/new_topic",
    response_model=Topic,
    status_code=status.HTTP_201_CREATED
)
@verify_session
async def create_new_topic(
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    new_topic:  Annotated[
        NewTopic,
        Body(
            title="New Topic",
            description="New topic data",
            examples=[
                {
                  "link_pub_key": "BASE64_ED25516_DER",
                  "link_pub_key_sig": "SIGNATURE",
                  "expires_ts": "DATETIME"
                }
            ]
        )
    ],
    db_session: DBSessionDep
):

    new_session.session_id = session_id

    # TODO verify message_pub_key_sig

    return await create_topic(db_session, new_topic)


@router.get("/{session_id}/topics",
    response_model=CollectionResponseModel[Topic]
)
@verify_session
async def get_topics(
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    db_session: DBSessionDep,
    limit:      int | None = Query(default=25, ge=1, le=25)
):

    topics, count, _ = await load_session_topics(db_session, session_id, limit=limit)

    return Collection(collection=topics, count=count, page=1, limit=limit)


@router.get("/{session_id}/topics/{topic_id}",
    response_model=TopicFull
)
@verify_session
async def get_topic_replies(
    db_session: DBSessionDep,
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    topic_id:   Annotated[str, Path(title="topic id",   pattern=UUID4_PATTERN)],
    limit:  int | None      = Query(default=10, ge=1, le=10),
    key_id: str | None      = Query(default=None),
    key_ts: datetime | None = Query(default=None)
):

    ret = await load_session_topic_replies(
        db_session,
        session_id,
        topic_id,
        limit=limit,
        key_id=key_id,
        key_ts=key_ts
    )

    if ret is None:
        raise APIException(status_code=404, detail=f"Topic not found")

    return ret


@router.post("/{session_id}/topics/{topic_id}/add_comment",
    response_model=ReplyComment,
    status_code=status.HTTP_201_CREATED
)
@verify_session
async def add_topic_reply_comment(
    db_session: DBSessionDep,
    response:   Response,
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    topic_id:   Annotated[str, Path(title="topic id",   pattern=UUID4_PATTERN)],
    new_comment: Annotated[
        NewReplyComment,
        Body(
            title="Reply Comment",
            description="Reply comment",
            examples=[
                {
                  "topic_reply_id": "UUID",
                  "data": "ENCRYPTED_DATA"
                }
            ]
        )
    ],
):

    session = await load_session(db_session, session_id)

    new_comment.session_key_id = session.key_id

    try:
        comment = await add_reply_comment(db_session, new_comment)
    except Exception as e:

        logger.warn(e)
        raise APIException(status_code=400, detail=f"Invalid Comment")


    return comment


@router.get("/{session_id}/replies",
    response_model=CollectionResponseModel[Topic]
)
@verify_session
async def get_sent(
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    db_session: DBSessionDep,
    limit:      int | None = Query(default=25, ge=1, le=25)
):

    session = await load_session(db_session, session_id)

    replies, count, _ = await load_session_replies(db_session, session.key_id, limit=limit)

    return Collection(collection=replies, count=count, page=1, limit=limit)


@router.get("/{session_id}/replies/{topic_id}",
    response_model=TopicFull
)
@verify_session
async def get_sent_topic_replies(
    session_id: Annotated[str, Path(title="session id", pattern=UUID4_PATTERN)],
    topic_id:   Annotated[str, Path(title="topic id", pattern=UUID4_PATTERN)],
    db_session: DBSessionDep,
    limit:      int | None      = Query(default=5, ge=1, le=10),
    key_id:     str | None      = Query(default=None),
    key_ts:     datetime | None = Query(default=None),
):
    """
    - session_id: session UUID
    - topic_id: topic UUID
    - limit: optional results per page, defaults to 10
    - key_id: After cursor id
    - key_ts: After cursor timestmap
    """

    session = await load_session(db_session, session_id)

    ret = await load_topic_with_replies(
        db_session,
        session.key_id,
        topic_id,
        limit=limit,
        key_id=key_id,
        key_ts=key_ts
    )

    if ret is None:
        raise APIException(status_code=404, detail=f"Reply not found")

    return ret

