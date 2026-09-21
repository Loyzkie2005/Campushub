import asyncio
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_chat.db"
os.environ["CHAT_JWT_SECRET"] = "test-only-secret-that-is-over-32-bytes"
os.environ["ALLOWED_ORIGINS"] = "http://testserver"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: E402,F401


async def reset_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    asyncio.run(reset_database())
    with TestClient(app) as test_client:
        yield test_client
