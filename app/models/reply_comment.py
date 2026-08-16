from datetime import datetime
import uuid

from sqlalchemy import (
    DateTime,
    func,
    ForeignKey,
    String,
    Text,
    text,
    Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, BYTEA

from . import Base


class ReplyComment(Base):
    __tablename__ = "reply_comment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    topic_reply_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('topic_reply.id'),
        nullable=False,
        unique=True
    )
    session_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('session.key_id'),
        nullable=False
    )
    created_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    data: Mapped[bytes] = mapped_column(BYTEA)
    reply: Mapped["TopicReply"] = relationship(back_populates="comment")


from .topic_reply import TopicReply
