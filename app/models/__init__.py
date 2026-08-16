from sqlalchemy.orm import declarative_base


Base = declarative_base()

from .session import Session
from .topic import Topic
from .topic_reply import TopicReply
from .reply_comment import ReplyComment
