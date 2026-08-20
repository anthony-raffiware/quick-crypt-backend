import os

os.environ['database_settings__pg_schema'] = 'cloud_app_testing'

import pytest
import pytest_asyncio
from pprint import pprint
import json
import base64
import uuid
from asyncio import current_task, TaskGroup
from typing import Generic, Type, Callable, TypeVar, Any, Optional, List, Annotated
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import async_scoped_session
from httpx import AsyncClient, ASGITransport

from app.api.v1 import app
from app.db import get_db_session, sessionmanager
from app.models import Base, Session, Topic, TopicReply
from app.config import Settings
from app.utils import load_private_key
#os.environ['database_settings__pg_schema'] = 'cloud_app_testing'


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def settings_overrides():

    os.environ['database_settings__pg_schema'] = 'cloud_app_testing'
    Settings().__init__() # Force reload

    yield Settings()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():

    sessionmanager.settings.pg_schema =  'cloud_app_testing'

    async with sessionmanager.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with sessionmanager.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def db_session(engine):

    async with sessionmanager.connect() as conn:
        async with sessionmanager.session() as session:
            yield session


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def api_client(engine):

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


def dump_response(response: Response):
    print(json.dumps(response.json(), indent=4))


def generate_ed25519_key():

    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    priv_der = priv_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    pub_der = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return (
       priv_key,
       base64.b64encode(priv_der).decode('utf-8'),
       base64.b64encode(pub_der).decode('utf-8')
    )


def generate_x25519_key():

    priv_key = x25519.X25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    priv_der = priv_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    pub_der = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return (
       priv_key,
       base64.b64encode(priv_der).decode('utf-8'),
       base64.b64encode(pub_der).decode('utf-8')
    )


AsyncScopedSession = async_scoped_session(
    sessionmanager._sessionmaker,
    scopefunc=current_task
)

# @pytest.mark.anyio(loop_scope="session")
@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def test_sessions():

    async with TaskGroup() as tg:

        session1 = tg.create_task(create_session("test_session1"))
        session2 = tg.create_task(create_session("test_session2"))
        session3 = tg.create_task(create_session("test_session3"))


    async with TaskGroup() as tg:

        tg.create_task(
            create_topic(
                session1.result(),
                [
                  ( session2.result(), 5 ),
                  ( session3.result(), 2 )
                ]
            )
        )
        tg.create_task(create_topic( session1.result(), [(session3.result(), 2 )] ))
        tg.create_task(create_topic( session3.result(), [(session2.result(), 1 )] ))


    return [(s.result()) for s in [session1, session2, session3]]


async def create_session(name:str):

    key, priv, pub = generate_ed25519_key()
    session = Session( session_pub_key=pub )

    async with AsyncScopedSession() as db_session:
        db_session.add(session)

        await db_session.flush()
        await db_session.refresh(session)

        #create_message(db_session, session)
        # priv_key, priv_der, pub_der = generate_x25519_key()

        # message = Message(
        #             session_id=session.id,
        #             message_pub_key=pub_der,
        #             message_pub_key_sig='TESTESTFIX'
        #           )

        # db_session.add(message)
        #session.messages.append(message)

        #await db_session.flush()
        #await db_session.refresh(message, ["message_parts"])
        await db_session.commit()

    return str(session.id), priv, str(session.key_id)


async def create_topic(
    for_session: Session,
    senders: List[List[Any]]
    # from_session: Session,
    # count: int=1
):

    *_, pub_der = generate_x25519_key()
    # *_, part_pub_der = generate_x25519_key()
    for_session_id, *_ = for_session
    # *_, from_session_key_id = from_session

    topic = Topic(
                session_id=for_session_id,
                topic_pub_key=pub_der,
                topic_pub_key_sig='TESTESTFIX',
                data=gen_junk_data(),
                replies=[
                    TopicReply(
                      session_key_id=s[2], # from_session_key_id,
                      topic_reply_pub_key=generate_x25519_key()[2],
                      topic_reply_pub_key_sig='TESTTESTFIX',
                      data=gen_junk_data()
                    )
                    # [j for j in y for _ in range(j)]
                    for (s, count) in senders for _ in range(count)


                    # for mp in ( [ s[0][2],    ] for fs in range(s[1]) ) for s in senders
                    #for m in range(count)
                ]
              )

    async with AsyncScopedSession() as db_session:
        db_session.add(topic)
        await db_session.commit()


def gen_junk_data(size: int = 256):

    return os.urandom(size)


#  response = await client.post(
#         "https://api.example.com/upload",
#         headers={"Content-Type": "application/json"},
#         json={"key": "value"}
#     )

# x-qcs-nonce f2o4q4zpQpvWACw1jgDgBzzJBgKu0oZpOyPNmpSgh/U=
#
# x-qcs-signature BFJuy8lVVwIIqMaWTM_4ycwvbC2gBrIAfyDKGSQsUvJi4ZaMmB3W-WXVURYuVhr32j7sm3Cn3gO59ArHyPraBA
#
# x-qcs-timestamp 2026-08-20 16:58:18 +00:00

async def sign_request(
    priv_key: str,
    func: Callable,
    path: str,
    headers={},
    **kwargs
):

    print(priv_key)
    headers.update({"QCS-Test": "weee"})

    key = load_private_key(priv_key)

    return await func(path, headers=headers, **kwargs)

