import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING
from .config import get_settings

# Module-level client and db — initialized once on startup
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    _db = _client[settings.mongodb_db_name]

    # Verify connection is alive
    await _client.admin.command("ping")

    # Ensure indexes exist (idempotent — safe to call on every startup)
    await _db.users.create_index("email", unique=True)
    await _db.users.create_index("username", unique=True)
    await _db.watched_content.create_index(
        [("user_id", ASCENDING), ("tmdb_id", ASCENDING)], unique=True
    )
    await _db.watched_content.create_index(
        [("user_id", ASCENDING), ("watched_at", ASCENDING)]
    )


async def close_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db
