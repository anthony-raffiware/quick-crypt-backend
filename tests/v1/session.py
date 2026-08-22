import pytest
import pytest_asyncio
from pprint import pprint
import asyncio
import logging
import uuid
import base64
from datetime import datetime
from pprint import pprint

from tests.utils import (
    dump_response,
    generate_ed25519_key,
    generate_x25519_key,
    gen_junk_data,
    sign_request
)
from app.api.v1 import app
from app.models import Base, Session, Topic, TopicReply
from app.crud.session import load_session
from app.config import Settings

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

logging.getLogger('sqlalchemy.engine.Engine').disabled = True


@pytest.mark.asyncio(loop_scope="session")
async def test_get_session(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]

    #response = await api_client.get(f"/session/{session_id}")
    response = await sign_request(test_sessions[0] ,
                         api_client.get, f"/session/{session_id}"
                     )
    dump_response(response)
    assert response.status_code == 200


    response = await api_client.get(f"/session/{session_id}")
    dump_response(response)
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_new_session(api_client, db_session):

    key, priv, pub = generate_ed25519_key()

    new_session = {"pub_key": pub}

    response = await api_client.post('/session/new', json=new_session)
    dump_response(response)
    assert response.status_code == 201

    session_id = response.json().get('data').get('id')

    response = await sign_request((session_id, priv, pub),
                         api_client.get, f"/session/{session_id}"
                     )
    dump_response(response)
    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_session_not_found(api_client, db_session):

    session_id=uuid.uuid4()

    response = await api_client.get(f"/session/{session_id}")
    dump_response(response)

    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_session_get_topics(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]

    response = await sign_request(test_sessions[0],
                         api_client.get, f"/session/{session_id}/topics",
                         params={"limit": 7 }
                     )
    dump_response(response)

    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_session_get_topic_parts(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]
    session2_id, *_ = test_sessions[1]

    session = await load_session(db_session, session_id)
    session2 = await load_session(db_session, session2_id)

    query = (
        select(Topic).
        join(TopicReply, and_(
            Topic.id == TopicReply.topic_id,
        )).
        where(
            and_(
                Topic.session_id == session.id,
                TopicReply.session_key_id == session2.key_id
            )
        )
    )

    topic = (await db_session.execute(query)).scalars().first()

    response = await sign_request(test_sessions[0],
                   api_client.get, f"/session/{session_id}/topics/{topic.id}"
               )
    dump_response(response)

    assert response.status_code == 200


    reply_ids = [ r['id'] for r in response.json()['data']['replies'] ]

    assert response.status_code == 200

    response = await sign_request(test_sessions[0],
                   api_client.get, f"/session/{session_id}/topics/{topic.id}",
                   params={"limit": 3}
               )
    dump_response(response)

    replies = response.json()['data']['replies']

    assert replies[0]['id'] == reply_ids[0]
    assert replies[1]['id'] == reply_ids[1]
    assert replies[2]['id'] == reply_ids[2]

    last = replies[2]

    response = await sign_request(test_sessions[0],
        api_client.get, f"/session/{session_id}/topics/{topic.id}",
        params={
            "limit": 3,
            "key_id": last['id'],
            "key_ts": last['created_ts'],
        }
    )
    dump_response(response)

    replies = response.json()['data']['replies']

    assert replies[0]['id'] == reply_ids[3]
    assert replies[1]['id'] == reply_ids[4]
    assert replies[2]['id'] == reply_ids[5]

    last = replies[2]

    response = await sign_request(test_sessions[0],
        api_client.get, f"/session/{session_id}/topics/{topic.id}",
        params={
            "limit": 3,
            "key_id": last['id'],
            "key_ts": last['created_ts'],
        }
    )
    dump_response(response)

    replies = response.json()['data']['replies']

    assert 1 == len(replies)
    assert replies[0]['id'] == reply_ids[6]


@pytest.mark.asyncio(loop_scope="session")
async def test_session_new_topic(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]

    priv_key, priv_der, pub_der = generate_x25519_key()

    # TODO session uuid + message uuid + x25519 pub key hash
    new_topic = {
        "session_id": str(session_id),
        "topic_pub_key": pub_der,
        "topic_pub_key_sig": "TESTESTESTFIX",
        "data": base64.urlsafe_b64encode(gen_junk_data()).decode('utf-8').rstrip('=')
    }

    response = await sign_request(test_sessions[0] ,
        api_client.post, f"/session/{session_id}/new_topic",
        json=new_topic
    )
    dump_response(response)

    assert response.status_code == 201


@pytest.mark.asyncio(loop_scope="session")
async def test_session_get_sent(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[1]

    session  = await load_session(db_session, session_id)
    response = await sign_request(test_sessions[1] ,
        api_client.get, f"/session/{session_id}"
    )
    dump_response(response)

    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_session_get_sent_parts(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]
    session2_id, *_ = test_sessions[1]
    session3_id, *_ = test_sessions[2]

    session = await load_session(db_session, session_id)
    session2 = await load_session(db_session, session2_id)
    session3 = await load_session(db_session, session3_id)

    query = (
        select(Topic).
        join(TopicReply, and_(
            Topic.id == TopicReply.topic_id,
        )).
        where(
            and_(
               Topic.session_id == session.id,
               TopicReply.session_key_id == session2.key_id
            )
        )
    )

    topic = (await db_session.execute(query)).scalars().first()

    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2_id}/replies/{topic.id}",
        params={"limit": 10 }
    )
    dump_response(response)

    reply_ids = [ r['id'] for r in response.json()['data']['replies'] ]

    assert response.status_code == 200

    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2_id}/replies/{topic.id}",
        params={"limit": 2}
    )
    dump_response(response)

    replies = response.json()['data']['replies']

    assert replies[0]['id'] == reply_ids[0]
    assert replies[1]['id'] == reply_ids[1]

    last = replies[1]

    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2_id}/replies/{topic.id}",
        params={
            "limit": 2,
            "key_id": last['id'],
            "key_ts": last['created_ts'],
        }
    )

    dump_response(response)

    replies = response.json()['data']['replies']

    assert replies[0]['id'] == reply_ids[2]
    assert replies[1]['id'] == reply_ids[3]

    last = replies[1]

    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2_id}/replies/{topic.id}",
        params={
            "limit": 2,
            "key_id": last['id'],
            "key_ts": last['created_ts'],
        }
    )
    dump_response(response)

    replies = response.json()['data']['replies']

    assert 1 == len(replies)
    assert replies[0]['id'] == reply_ids[4]


@pytest.mark.asyncio(loop_scope="session")
async def test_session_add_reply_comment(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]
    session2_id, *_ = test_sessions[1]

    session  = await load_session(db_session, session_id)
    session2 = await load_session(db_session, session2_id)

    query = (
        select(Topic)
        .join(TopicReply, and_(
            Topic.id == TopicReply.topic_id,
        ))
        .options(
            selectinload(Topic.replies),
        )
        .where(
            and_(
                Topic.session_id == session.id,
                TopicReply.session_key_id == session2.key_id
            )
        )
    )

    topic       = (await db_session.execute(query)).scalars().first()
    mock_data   = base64.b64encode(gen_junk_data()).decode('utf-8')
    new_comment = {
        "topic_reply_id": str(topic.replies[0].id),
        "data": mock_data
    }

    response = await sign_request(test_sessions[0],
        api_client.post, f"/session/{session_id}/topics/{topic.id}/add_comment",
        json=new_comment
    )
    dump_response(response)

    assert response.status_code == 201

    edited_mock_data = base64.b64encode(gen_junk_data()).decode('utf-8')
    new_comment = {
        "topic_reply_id": str(topic.replies[0].id),
        "data": edited_mock_data
    }

    response = await sign_request(test_sessions[0],
        api_client.post, f"/session/{session_id}/topics/{topic.id}/add_comment",
        json=new_comment
    )
    dump_response(response)

    assert response.status_code == 201

    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2_id}/replies/{topic.id}",
        params={"limit": 10}
    )

    dump_response(response)

@pytest.mark.asyncio(loop_scope="session")
async def test_session_last_topic_update(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]

    session  = await load_session(db_session, session_id)

    response = await sign_request(test_sessions[0],
        api_client.get, f"/session/{session_id}/topics/last_update",
    )
    dump_response(response)

    assert response.status_code == 200


    key, priv, pub = generate_ed25519_key()

    new_session_data = {"pub_key": pub}

    response = await api_client.post('/session/new', json=new_session_data)
    dump_response(response)
    assert response.status_code == 201

    new_session_id = response.json().get('data').get('id')
    new_session = await load_session(db_session, new_session_id)

    response = await sign_request((new_session_id, priv, ''),
        api_client.get, f"/session/{new_session_id}/topics/last_update",
    )
    dump_response(response)

    assert response.status_code == 200
