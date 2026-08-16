from typing import List
from datetime import datetime
import uuid

from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, BYTEA


from . import Base

class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True
    )
    session_pub_key: Mapped[str]
    created_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    data: Mapped[bytes] = mapped_column(BYTEA, nullable=True)
    topics: Mapped[List["Topic"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
