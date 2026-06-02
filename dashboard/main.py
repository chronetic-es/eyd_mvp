import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from queries import (
    get_calls_overview, get_calls_by_motive, get_calls_timeline,
    get_active_incidents, get_incident_zones,
    get_billing_summary, get_overdue_bills, get_active_expedients,
    get_work_orders_summary, get_recent_work_orders,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")

DATABASE_URL = os.getenv("DATABASE_URL", "")

pool: asyncpg.Pool | None = None


async def _create_pool(max_retries: int = 10) -> asyncpg.Pool | None:
    """Try to create the DB connection pool with incremental backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            p = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
            logger.info("Connected to database (attempt %d)", attempt)
            return p
        except Exception as exc:
            logger.warning("DB connection attempt %d/%d failed: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                await asyncio.sleep(attempt)  # 1s, 2s, 3s ...
    logger.error("Could not connect to database after %d attempts — starting without DB", max_retries)
    return None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global pool
    pool = await _create_pool()
    yield
    if pool:
        await pool.close()
        logger.info("Database pool closed")


app = FastAPI(title="EYD Dashboard", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"


def _require_pool():
    if pool is None:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    return None


# ─── HEALTH ─────────────────────────────────────────────

@app.get("/health")
async def health():
    db_ok = False
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_ok = True
        except Exception:
            pass
    return {"status": "ok", "db": db_ok}


# ─── CALLS ───────────────────────────────────────────────

@app.get("/api/calls/overview")
async def calls_overview():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_calls_overview(conn)


@app.get("/api/calls/motives")
async def calls_motives():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_calls_by_motive(conn)


@app.get("/api/calls/timeline")
async def calls_timeline():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_calls_timeline(conn)


# ─── INCIDENTS ───────────────────────────────────────────

@app.get("/api/incidents/active")
async def incidents_active():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_active_incidents(conn)


@app.get("/api/incidents/zones")
async def incidents_zones():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_incident_zones(conn)


# ─── BILLING ─────────────────────────────────────────────

@app.get("/api/billing/summary")
async def billing_summary():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_billing_summary(conn)


@app.get("/api/billing/overdue")
async def billing_overdue():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_overdue_bills(conn)


@app.get("/api/billing/expedients")
async def billing_expedients():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_active_expedients(conn)


# ─── WORK ORDERS ─────────────────────────────────────────

@app.get("/api/work-orders/summary")
async def work_orders_summary():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_work_orders_summary(conn)


@app.get("/api/work-orders/recent")
async def work_orders_recent():
    if err := _require_pool():
        return err
    async with pool.acquire() as conn:
        return await get_recent_work_orders(conn)


# ─── STATIC FILES ────────────────────────────────────────

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")
