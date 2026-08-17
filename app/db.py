from typing import Any, AsyncIterator, Tuple
import contextlib
import asyncio
from asyncio import Future

from sqlalchemy import create_engine, event, select, func
from sqlalchemy.ext.asyncio import (
  create_async_engine,
  async_sessionmaker,
  AsyncSession,
  AsyncConnection,
  AsyncEngine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import Select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.result import ScalarResult

from app.config import Settings

DBSettings = Settings().database_settings


class DatabaseSessionManager:


    def __init__(self):

        self.settings = DBSettings
        self._engine  = self.get_async_engine()
        self._sessionmaker = async_sessionmaker(
                                 autocommit=False,
                                 bind=self._engine,
                                 expire_on_commit=False
                             )


    def get_db_url(self) -> str:

        settings = self.settings
        host     = settings.host
        port     = settings.port
        db       = settings.database
        user     = settings.user
        password = settings.password

        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

        return url


    def get_async_engine(self) -> AsyncEngine:

        settings = self.settings
        schema   = settings.pg_schema
        url      = self.get_db_url();

        engine = create_async_engine(
                   url,
                   connect_args={
                       "server_settings": {"search_path": schema}
                   },
                   echo=settings.debug,
                   pool_pre_ping=True,
                   pool_size=settings.pool_size,
                   max_overflow=settings.max_overflow,
                   pool_recycle=settings.pool_recycle
                )

        return engine


    async def close(self):

        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None


    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:

        settings = self.settings
        schema   = settings.pg_schema

        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise


    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:

        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()

        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager()


async def get_db_session() -> AsyncIterator[AsyncSession]:

    async with sessionmanager.session() as session:
        yield session


async def collection_result(
    db_session: 'DBSessionDep',
    query: Select,
    limit: int = 10
) -> Tuple[ScalarResult, int, int]:

    count_stmt = select(func.count()).select_from(query.subquery())

    count   = await db_session.scalar(count_stmt)
    results = await db_session.scalars(query.limit(limit))

    return results, count, limit
