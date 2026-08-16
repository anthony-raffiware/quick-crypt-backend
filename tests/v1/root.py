from pprint import pprint

from fastapi.testclient import TestClient
from tests.utils import dump_response

from app.api.v1 import app
from app.config import Settings

DBSettings = Settings().database_settings


client = TestClient(app)


def test_read_root():
    response = client.get("/")
    #pprint(response)
    dump_response(response)
    assert response.status_code == 404
    #assert response.json() == {
    #    "id": "foo",
    #    "title": "Foo",
    #    "description": "There goes my hero",
    #}

def test_get_test():
    response = client.get("/test")
    #pprint(response)
    dump_response(response)
    assert response.status_code == 200

def test_get_test_list():
    response = client.get("/test_list")
    #pprint(response)
    dump_response(response)
    assert response.status_code == 200

def test_error_handler():

    response = client.get("/error")
    dump_response(response)
    assert response.status_code == 500

def test_config():
   pprint(DBSettings)

