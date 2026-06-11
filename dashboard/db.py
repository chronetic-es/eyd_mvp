"""Database pool management and FastAPI connection dependency."""
import asyncio
import logging
import os

import asyncpg

logger = logging.getLogger("dashboard")

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Module-level pool, populated in the background after startup.
_pool: asyncpg.Pool | None = None


def get_pool() -> asyncpg.Pool | None:
    return _pool


async def connect_with_retries():
    """Create the DB pool in background with retries — never blocks startup."""
    global _pool
    for attempt in range(1, 11):
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=8)
            logger.info("Connected to database (attempt %d)", attempt)
            return
        except Exception as exc:
            logger.warning("DB connection attempt %d/10 failed: %s", attempt, exc)
            await asyncio.sleep(2)
    logger.error("Could not connect to database after 10 attempts")


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_conn():
    """FastAPI dependency: yields a pooled connection, or raises 503 if no DB."""
    from fastapi import HTTPException

    pool = get_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    async with pool.acquire() as conn:
        yield conn
