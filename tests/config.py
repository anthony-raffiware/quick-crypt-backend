from pprint import pprint

from app.config import Settings

def test_config_load():

    config = Settings()
    pprint(config.database_settings.host)
