from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

#from .message import Message
from .core import SerializedBinaryData

class NewSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pub_key: str


class Session(BaseModel, SerializedBinaryData):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key_id: UUID
    session_pub_key: str
    created_ts: datetime
    topics: List["Topic"] = Field(default=[])
    data: Optional[bytes]


from .topic import Topic
Session.update_forward_refs()
