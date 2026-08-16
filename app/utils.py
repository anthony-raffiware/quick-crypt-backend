import uuid
import re

UUID4_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[a-fA-F0-9]{3}-[89abAB][a-fA-F0-9]{3}-[0-9a-fA-F]{12}$')

def generate_uuid_id(length: int = 16) -> str:
    return uuid.uuid4().hex[:length]

# SELECT
#    topic.id,
#    topic.session_id,
#    topic.topic_pub_key,
#    topic.topic_pub_key_sig,
#    topic.created_ts,
#    topic.updated_ts,
#    topic.expires_ts,
#    topic.data
# FROM
#   topic
# JOIN (
#   SELECT
#     topic_reply.topic_id AS topic_id,
#     max(topic_reply.created_ts) AS last_reply_date
#   FROM
#     topic_reply
#   WHERE
#     topic_reply.session_key_id = $1::UUID
#   GROUP BY
#     topic_reply.topic_id
# )
# AS
#   anon_1
# ON
#   topic.id = anon_1.topic_id, topic_reply
# WHERE
#   topic_reply.session_key_id = $2::UUID
# GROUP BY
#   topic.id, anon_1.last_reply_date
# ORDER BY anon_1.last_reply_date DESC
