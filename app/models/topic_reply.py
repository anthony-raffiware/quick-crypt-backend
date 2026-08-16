from typing import List
from datetime import datetime
import uuid

from sqlalchemy import (
    DateTime,
    func,
    ForeignKey,
    String,
    Text,
    text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, BYTEA


from . import Base


class TopicReply(Base):
    __tablename__ = "topic_reply"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('topic.id'),
        nullable=False
    )
    session_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('session.key_id'),
        nullable=False
    )
    topic_reply_pub_key: Mapped[str]
    topic_reply_pub_key_sig: Mapped[str]
    data: Mapped[bytes] = mapped_column(BYTEA)
    created_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    expires_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + text("INTERVAL '1 week'")
    )
    topic: Mapped["Topic"] = relationship(back_populates="replies")
    comment: Mapped["ReplyComment"] = relationship(
        back_populates="reply",
        uselist=False,
    )

from .reply_comment import ReplyComment
