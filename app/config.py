from typing import Generic, Type, Callable, TypeVar, Any, Optional, List, Annotated

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    JsonConfigSettingsSource
)
from typing import Tuple, Type


class APISettingsCores(BaseModel):
    allow_origins: List[str] = Field(description='CORS allow-origins', default=[])
    allow_credentials: bool  = Field(description='CORS allow-credentials', default=False )
    allow_methods: List[str] = Field(description='CORS allow-methods', default=["*"])
    allow_headers: List[str] = Field(description='CORS allow-headers', default=["*"])


class APISettings(BaseModel):
    cores: APISettingsCores
    base_path: str = Field(description='Base URL', default='')


class DatabaseSettings(BaseModel):

    host: str         = Field(description='host')
    port: int         = Field(description='port')
    database: str     = Field(description='database')
    pg_schema: str    = Field(description='schema')
    user: str         = Field(description='user')
    password: str     = Field(description='password')
    pool_size: int    = Field(description='DB connection pool size', default=10)
    max_overflow: int = Field(description='DB burst connections', default=10)
    pool_recycle: int = Field(description='DB connection recycle timeout', default=600)
    debug: bool       = Field(description='Enable debugging', default=False)

class Settings(BaseSettings):

    api_settings: APISettings
    database_settings: DatabaseSettings

    model_config = SettingsConfigDict(
                       env_nested_delimiter="__",
                       json_file="config.json",
                       json_file_encoding="utf-8"
                   )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ) -> Tuple:

        return (
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls),
        )
