import os
import secrets
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv as load_env
from decouple import config
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings

load_env('dev.env')


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = 'MiroAPI'
    POSTGRES_USER: str = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD: str = load_env('POSTGRES_PASSWORD')
    POSTGRES_DB: str = os.environ.get('POSTGRES_DB')
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('POSTGRES_URL')
    USERS_OPEN_REGISTRATION: bool = False
    DEBUG: str = os.environ.get('DEBUG', True)
    HOST: str = config('HOST', default='0.0.0.0')
    PORT: int = config('PORT', cast=int, default=8000)
    TIMEZONE: str = 'Chile/Continental'
    ALLOW_ORIGINS: list[str] = ['*']
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: list[str] = ['*']
    ALLOW_HEADERS: list[str] = ['*']
    EXPOSE_HEADERS: str = ''
    MAX_AGE: str = ''
    page_size: int = 10
    current_page: int = 1
    VERSION: dict[int, str] = {1: '/v1'}
    CURRENT_VERSION: str = str(list(VERSION.keys())[-1]) + '.0.0'
    TAGS_V1_METADATA: list[dict[str, str]] = [{"name": "MiroAPI v1", "description": "MiroAPI version 1.0.0."}]
    TAGS_METADATA: list[dict[str, str]] = TAGS_V1_METADATA

    class Config:
        case_sensitive = True


def assemble_cors_origins(v: Union[str, List[str]]) -> Union[List[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


def assemble_db_connection(v: Optional[str], values: Dict[str, Any]) -> Any:
    if isinstance(v, str):
        return v
    return PostgresDsn.build(
        scheme="postgresql",
        user=values.get("POSTGRES_USER"),
        password=values.get("POSTGRES_PASSWORD"),
        host=values.get("HOST", "127.0.0.1"),
        path=f"/{values.get('POSTGRES_DB') or ''}",
    )


# Apply the field validators to the corresponding fields
Settings.__annotations__['BACKEND_CORS_ORIGINS'] = assemble_cors_origins
Settings.__annotations__['SQLALCHEMY_DATABASE_URI'] = assemble_db_connection

# Create an instance of Settings
settings = Settings()
