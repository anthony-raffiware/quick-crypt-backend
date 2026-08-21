import pytest
import pytest_asyncio
import asyncio
import logging
import uuid
import base64
from datetime import datetime
from pprint import pprint

from tests.utils import(
  dump_response,
  generate_x25519_key,
  gen_junk_data,
  sign_request
)
from app.api.v1 import app
from app.models import Base, Session, Topic, TopicReply
from app.crud.session import create_session, load_session
from app.crud.topics import get_session_topic_results


logging.getLogger('sqlalchemy.engine.Engine').disabled = True


@pytest.mark.asyncio(loop_scope="session")
async def test_topic_reply(api_client, db_session, test_sessions):

    session_id, *_ = test_sessions[0]
    session2_id, *_ = test_sessions[1]

    session = await load_session(db_session, session_id)
    session2 = await load_session(db_session, session2_id)

    topic = (await get_session_topic_results(db_session, session_id))[0].first()

    priv_key, priv_der, pub_der = generate_x25519_key()
    mock_data = base64.b64encode(gen_junk_data()).decode('utf-8')

    new_reply = {
        "session_key_id": str(session.key_id),
        "topic_reply_pub_key": pub_der,
        "topic_reply_pub_key_sig": "TESTESTESTFIX",
        "data": mock_data
    }

    response = await sign_request(test_sessions[0],
        api_client.post, f"/topic/{topic.id}/send_reply/{session_id}",
        json=new_reply
    )
    dump_response(response)

    assert response.status_code == 201

    #response = await api_client.get(f"/session/{session2.id}/replies/{topic.id}")
    response = await sign_request(test_sessions[1],
        api_client.get, f"/session/{session2.id}/replies/{topic.id}"
    )
    dump_response(response)

    assert response.status_code == 200
