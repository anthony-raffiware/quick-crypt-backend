from typing import List
from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, BYTEA


from . import Base


class Topic(Base):
    __tablename__ = "topic"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, # server_default=text("gen_random_uuid()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('session.id'),
        nullable=False
    )
    topic_pub_key: Mapped[str]
    topic_pub_key_sig: Mapped[str] # session uuid + message uuid + key hash
    created_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    expires_ts:  Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + text("INTERVAL '1 week'")
    )
    data: Mapped[bytes] = mapped_column(BYTEA)
    session: Mapped["Session"] = relationship( back_populates="topics")
    replies: Mapped[List["TopicReply"]] = relationship(
        back_populates="topic",
        order_by="desc(TopicReply.created_ts)",
        cascade="all, delete-orphan"
    )

from .topic_reply import TopicReply
