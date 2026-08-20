import pytest
import pytest_asyncio
from tests.utils import (
    generate_ed25519_key,
    generate_x25519_key,
)
from pprint import pprint
import asyncio
import logging
import uuid
import base64
from datetime import datetime
from pprint import pprint

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.utils import load_public_key, verify_tokens, sign_tokens


test_vectors = [
    #{
    #  "tokens": {
    #     "sessionUuid": '82c2efea-7a36-4eac-83ec-e5ae27aaad43',
    #     "date": '2026-08-20 13:13:48 +00:00',
    #     "nonce": 'qWwNBjvp1sRmRqlF+Qs9WH3Jof65U/SInQOAIVcU58A='
    #  },
    #  "sig": 'YZtN37OzH0SsCwtguGeSC8OiKtgNljCSf_n85gxgjpw893knYPhZiCbmrILWwS3sNFeEROfFQIBpc34ClSPCDA'
    #}

    {
        "tokens": {
            "sessionUuid": '82c2efea-7a36-4eac-83ec-e5ae27aaad43',
            "date": '2026-08-20 13:41:05 +00:00',
            "nonce": 'Jy2+qrSKYKLAkPYCdugJxslEgHSW1F6keAA8GXrDRjs='
        },
        "sig": '_d2W1r5DGUxtWxFS-YgOdEj9N9rsKozXTZW2AzLjusbgmkqeunu3eTe3X0i7rmnIVpG7tHDC2kVSZTUuebQrAg',
        "pub_key": 'MCowBQYDK2VwAyEAB2V4r7cSqTC1zhzKEO5aTeD4Vp83xU0iUhDRufR4wqw'

    }
]


def test_load_public_key():

    vector = test_vectors[0]
    pub_key = vector['pub_key']

    key = load_public_key(pub_key)

    assert isinstance(key, Ed25519PublicKey)


def test_verify_tokens():


    vector  = test_vectors[0]
    tokens  = vector['tokens']
    sig     = vector['sig']
    pub_key = vector['pub_key']

    verified = verify_tokens(tokens, sig, pub_key)

    assert verified

    bad_tokens = {
        "sessionUuid": '82c2efea-7a36-4eac-83ec-e5ae27aaad43',
        "date": '2026-08-20 13:41:05 +00:01',
        "nonce": 'Jy2+qrSKYKLAkPYCdugJxslEgHSW1F6keAA8GXrDRjs='
    }

    not_verified = verify_tokens(bad_tokens, sig, pub_key)

    assert not not_verified


def test_sign_tokens():

    key, priv_key_enc, pub_key_enc = generate_ed25519_key()

    tokens = {
        "sessionUuid": '82c2efea-7a36-4eac-83ec-e5ae27aaad43',
        "date": '2026-08-20 13:41:05 +00:01',
        "nonce": 'Jy2+qrSKYKLAkPYCdugJxslEgHSW1F6keAA8GXrDRjs='
    }

    sig = sign_tokens(tokens, priv_key_enc)

    assert sig

    verified = verify_tokens(tokens, sig, pub_key_enc)

    assert verified

    btokens = {
        "sessionUuid": '82c2efea-7a36-4eac-83ec-e5ae27aaad43',
        "date": '2026-08-20 13:41:05 +00:02',
        "nonce": 'Jy2+qrSKYKLAkPYCdugJxslEgHSW1F6keAA8GXrDRjs='
    }

    bsig = sign_tokens(tokens, priv_key_enc)

    not_verified = verify_tokens(btokens, bsig, pub_key_enc)

    assert not not_verified
