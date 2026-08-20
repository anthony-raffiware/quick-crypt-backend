import names
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import DBSessionDep
from app.models import Session


async def create_session(
    db_session: DBSessionDep,
    key: str,
) -> Session:

    session = Session(session_pub_key=key)

    db_session.add(session)

    await db_session.flush()
    await db_session.refresh(session, ["topics"])
    await db_session.commit()

    return session


async def get_session_key(
    db_session: DBSessionDep,
    session_id: str
) -> str:

    query = (
        select(Session.session_pub_key)
        .where(Session.id == uuid.UUID(session_id))
    )

    session_key = (await db_session.execute(query)).scalars().first()

    return session_key

async def load_session(
    db_session: DBSessionDep,
    session_id: str
) -> Session:

    query = (
        select(Session)
        .where(Session.id == uuid.UUID(session_id))
        .options(selectinload(Session.topics))
    )

    session = (await db_session.execute(query)).scalars().first()

    return session
