import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def async_client():
    mongo_client = AsyncMongoMockClient()
    test_db = mongo_client["todo_app_test"]

    app.dependency_overrides[get_db] = lambda: test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    mongo_client.close()
