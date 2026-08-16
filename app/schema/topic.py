import base64
from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer

from .session import Session
from .core import SerializedBinaryData


class NewTopic(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    session_id: Optional[UUID] = None
    topic_pub_key: str
    topic_pub_key_sig: str
    expires_ts: Optional[datetime] = None


class Topic(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_pub_key: str
    topic_pub_key_sig: str
    created_ts: datetime
    updated_ts: datetime
    expires_ts: datetime


class NewTopicReply(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    session_key_id: UUID
    topic_id: Optional[UUID] = None
    topic_reply_pub_key: str
    topic_reply_pub_key_sig: str


class NewReplyComment(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    topic_reply_id: UUID
    session_key_id: Optional[UUID] = None


class ReplyComment(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_reply_id: UUID
    session_key_id: UUID
    created_ts: datetime


class TopicReply(BaseModel, SerializedBinaryData):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID
    session_key_id: UUID
    topic_reply_pub_key: str
    topic_reply_pub_key_sig: str
    created_ts: datetime
    expires_ts: datetime
    comment: Optional[ReplyComment] = Field(default=None, description="User email")


class TopicFull(Topic):

    replies: List["TopicReply"] = Field(default=[])


class TopicReplyFull(TopicReply):

    topic: Topic
