from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Python Todo Management App"
    app_port: int = Field(default=8000, alias="APP_PORT")
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        alias="MONGODB_URI",
    )
    mongodb_db_name: str = Field(default="todo_management", alias="MONGODB_DB_NAME")
    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
