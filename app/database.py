from typing import Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global _client, _database

    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    await _client.admin.command("ping")
    _database = _client[settings.mongodb_db_name]


async def close_mongo_connection() -> None:
    global _client, _database

    if _client is not None:
        _client.close()

    _client = None
    _database = None


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not connected",
        )
    return _database


def get_db() -> AsyncIOMotorDatabase:
    return get_database()
