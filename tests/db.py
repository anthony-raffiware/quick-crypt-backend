import pytest
import pytest_asyncio

from pprint import pprint
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, select

from app.db import get_db_session, sessionmanager
#from app.db import get_async_engine, get_async_session


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "test_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))



# @pytest_asyncio.fixture(scope="session", loop_scope="session")
# async def engine():
#     eng = get_async_engine()
#     async with eng.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#     yield eng
#     print('TEAR DOWN')
#
#     async with eng.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#
#     await eng.dispose()

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():

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

# @pytest_asyncio.fixture(scope="function", loop_scope="session")
# async def db_session2(engine):
#
#     async with engine.connect() as connection:
#         transaction = await connection.begin()
#
#         session_factory = async_sessionmaker(
#                              engine,
#                              class_=AsyncSession,
#                              expire_on_commit=False
#                           )
#
#         session = session_factory(bind=connection)
#         # Start a nested transaction (savepoint)
#         await session.begin_nested()
#         print('START SESS')
#         yield session
#         print('ROLLBACK!')
#
#         # Rollback to savepoint after test
#         await session.rollback()
#         await session.close()
#         await transaction.rollback()
#         await connection.close()
#
#    #  async with session_factory() as session:
#    #      print('START SESS')
#    #      yield session
#    #      print('ROLLBACK!')
#    #      await session.rollback()


# @pytest_asyncio.fixture
# async def async_db_setup(db_session):
#
#     engine =  get_async_engine()
#
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#
#
#     yield engine
#
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)



#def test_get_async_engine():
#
#    engine =  get_async_engine()
#    pprint(engine)
#

@pytest.mark.asyncio(loop_scope="session")
async def test_get_async_session(db_session):

    new_user = User(name="Alice")
    db_session.add(new_user)
    await db_session.commit()

    result = await db_session.execute(select(User))
    users = result.scalars().all()
    print([u.name for u in users])

@pytest.mark.asyncio(loop_scope="session")
async def test_get_async_session2(db_session):

    result = await db_session.execute(select(User))
    users = result.scalars().all()
    print([u.name for u in users])


