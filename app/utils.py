import uuid
import base64
import re
import logging
import inspect
from typing import List, Annotated, Generic, TypeVar, Optional, Dict, AnyStr
from pprint import pprint
from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer

#from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    load_der_private_key,
    load_der_public_key
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
  Ed25519PrivateKey,
  Ed25519PublicKey
)
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger("quick-crypt")

UUID4_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[a-fA-F0-9]{3}-[89abAB][a-fA-F0-9]{3}-[0-9a-fA-F]{12}$')


def generate_uuid_id(length: int = 16) -> str:
    return uuid.uuid4().hex[:length]


def verify_tokens(tokens: Dict, signature: str, pub_key: str) -> bool:

    key      = load_public_key(pub_key)
    msg      = getMessage_from_tokens(tokens)
    sig_data = decode_base64_url(signature)
    msg_data = bytes(msg, 'utf-8')

    try:

        key.verify(sig_data, msg_data)

        return True
    except InvalidSignature:
        return False
    except Exception as e:

        logger.error(f"Unexpected Signature Verification Error: {e}")
        raise


def sign_tokens(tokens: Dict, priv_key_enc: str) -> str:

    key = load_private_key(priv_key_enc)
    msg = getMessage_from_tokens(tokens)
    msg_data = bytes(msg, 'utf-8')

    try:

        sig = key.sign(msg_data)

        return encode_base64_url(sig)

    except Exception as e:

        logger.error(f"Unexpected Signing Error: {e}")
        raise


def getMessage_from_tokens(tokens: Dict) -> str:

    return ",".join([tokens[k] for k in sorted(tokens)])



def load_private_key(encoded_key: str) -> Ed25519PrivateKey:

    key_der = decode_base64_url(encoded_key)

    return load_der_private_key(key_der, password=None)


def load_public_key(encoded_key: str) -> Ed25519PublicKey:

    key_der = decode_base64_url(encoded_key)

    return load_der_public_key(key_der)


def encode_base64_url(raw_text: str) -> AnyStr:

    return base64.urlsafe_b64encode(raw_text).decode('utf-8').rstrip('=')


def decode_base64_url(base64url: str) -> AnyStr:

    padded_string = base64url + '=' * (-len(base64url) % 4)

    return base64.urlsafe_b64decode(padded_string)


def check_param(func, param_name):

    sig    = inspect.signature(func)
    params = sig.parameters

    if param_name in params:

        param = params[param_name]
        # param.kind : POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, KEYWORD_ONLY, VAR_KEYWORD
        return True, param.kind

    return False, None
