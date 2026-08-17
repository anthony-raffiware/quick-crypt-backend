import uuid
import re

UUID4_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[a-fA-F0-9]{3}-[89abAB][a-fA-F0-9]{3}-[0-9a-fA-F]{12}$')

def generate_uuid_id(length: int = 16) -> str:
    return uuid.uuid4().hex[:length]
