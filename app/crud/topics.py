import uuid
from typing import Any, Tuple, List
from datetime import datetime

from sqlalchemy import select, func, and_, tuple_
from sqlalchemy.orm import (
    selectinload,
    joinedload,
    with_parent,
    contains_eager,
    aliased
)
from sqlalchemy.sql.expression import Select
from sqlalchemy.engine.result import ScalarResult

from app.api.v1.dependencies import DBSessionDep
from app.models import Topic, TopicReply, ReplyComment
from app.schema.topic import NewTopic, NewTopicReply, NewReplyComment
from app.db import collection_result


async def load_topic(
    db_session: DBSessionDep,
    topic_id: str
) -> Topic:

    query = (
        select(Topic)
        .where(Topic.id == uuid.UUID(topic_id))
    )

    return (await db_session.execute(query)).scalars().one()


async def get_session_topic_results(
    db_session: DBSessionDep,
    session_id: str,
    **params: Any
) -> Tuple[ScalarResult, int, int]:

    query = (
        select(Topic)
        .where(Topic.session_id == uuid.UUID(session_id))
        .options(selectinload(Topic.replies))
        .order_by(Topic.updated_ts.desc())
        .limit(params.get('limit'))
    )

    return await collection_result( db_session, query, **params )


async def load_session_topics(
    db_session: DBSessionDep,
    session_id: str,
    **params: Any
) -> Tuple[List[Topic], int, int]:

    topics, count, limit = (await get_session_topic_results(db_session, session_id, **params))

    return topics.all(), count, limit


async def load_session_topic_replies(
    db_session: DBSessionDep,
    session_id: str,
    topic_id: str,
    **params: Any
) -> Topic:

    key_id = params.get('key_id')
    key_ts = params.get('key_ts')

    subq_conds = [
      TopicReply.topic_id == topic_id
    ]

    if None not in (key_id, key_ts):
        subq_conds.extend([
            tuple_(TopicReply.created_ts, TopicReply.id) < (key_ts, key_id)
        ])

    subq = (
        select(TopicReply)
        .join(TopicReply.comment, isouter=True)
        .where(
            *subq_conds
        )
        .order_by(TopicReply.created_ts.desc(), TopicReply.id.desc())
        .limit(params.get('limit'))
        .subquery()
        .lateral()
    )

    query = (
        select(Topic)
        .outerjoin(subq)
        .where(
            Topic.session_id == session_id,
            Topic.id == topic_id
        )
        .options(
            contains_eager(Topic.replies, alias=subq)
            .selectinload(TopicReply.comment),
        )
    )

    return (await db_session.execute(query)).scalars().first()


async def get_session_replies_results(
    db_session: DBSessionDep,
    session_key_id: str,
    **params: Any
) -> Tuple[ScalarResult, int, int]:

    last_reply = (
        select(
           TopicReply.topic_id,
           func.max(TopicReply.created_ts).label('last_reply_date')
        )
        .where(TopicReply.session_key_id == session_key_id )
        .group_by(TopicReply.topic_id)
        .subquery()
        .lateral()
    )

    query = (
        select(Topic)
        .join(last_reply,
            Topic.id == last_reply.c.topic_id,
        )
        .where(TopicReply.session_key_id == session_key_id)
        .order_by(last_reply.c.last_reply_date.desc())
        .group_by(Topic.id, last_reply.c.last_reply_date)
    )

    return await collection_result( db_session, query, **params )


async def load_session_replies(
    db_session: DBSessionDep,
    session_key_id: str,
    **params: Any
) -> Tuple[List[Topic], int, int]:

    replies, count, limit = (await get_session_replies_results(db_session, session_key_id, **params))

    return replies.all(), count, limit


async def load_topic_with_replies(
    db_session: DBSessionDep,
    session_key_id: str,
    topic_id: str,
    **params: Any
) -> Topic:

    key_id = params.get('key_id')
    key_ts = params.get('key_ts')

    subq_conds = [
        TopicReply.topic_id == topic_id,
        TopicReply.session_key_id == session_key_id
    ]

    if None not in (key_id, key_ts):
        subq_conds.extend([
            tuple_(TopicReply.created_ts, TopicReply.id) < (key_ts, key_id)
        ])

    subq = (
        select(TopicReply)
        .join(TopicReply.comment, isouter=True)
        .where(
            *subq_conds
        )
        .order_by(TopicReply.created_ts.desc(), TopicReply.id.desc())
        .limit(params.get('limit'))
        .subquery()
        .lateral()
    )

    query = (
        select(Topic)
        .outerjoin(subq)
        .where(
            Topic.id == topic_id,
        )
        .options(
            contains_eager(Topic.replies, alias=subq)
            .selectinload(TopicReply.comment)
        )
    )

    return (await db_session.execute(query)).scalars().first()


async def create_topic(
    db_session: DBSessionDep,
    new_topic: NewTopic
) -> Topic:

    topic = Topic(
        session_id=new_topic.session_id,
        topic_pub_key=new_topic.topic_pub_key,
        topic_pub_key_sig=new_topic.topic_pub_key_sig,
        data=new_topic.data
    )

    db_session.add(topic)

    await db_session.flush()
    await db_session.refresh(topic, ["replies"])
    await db_session.commit()

    return topic


async def add_topic_reply(
    db_session: DBSessionDep,
    session_id: str,
    new_reply: NewTopicReply
) -> TopicReply:

    reply = TopicReply(
        topic_id=new_reply.topic_id,
        session_key_id=new_reply.session_key_id,
        topic_reply_pub_key=new_reply.topic_reply_pub_key,
        topic_reply_pub_key_sig=new_reply.topic_reply_pub_key_sig,
        data=new_reply.data
    )

    db_session.add(reply)

    await db_session.flush()
    await db_session.refresh(reply, attribute_names=['comment'])

    topic = await load_topic(db_session, str(reply.topic_id))
    topic.updated_ts = func.now()

    await db_session.commit()

    return reply


async def add_reply_comment(
    db_session: DBSessionDep,
    new_comment: NewReplyComment
) -> ReplyComment:

    comment = ( await db_session\
                .execute(
                    select(ReplyComment)
                    .where(ReplyComment.topic_reply_id == new_comment.topic_reply_id)
                )
              )\
              .scalars().first()

    if comment:

        comment.data       = new_comment.data
        comment.created_ts = func.now()
    else:

        comment = ReplyComment(
            topic_reply_id=new_comment.topic_reply_id,
            session_key_id=new_comment.session_key_id,
            data=new_comment.data
        )

        db_session.add(comment)

    await db_session.flush()
    await db_session.refresh(comment)
    await db_session.commit()

    return comment
