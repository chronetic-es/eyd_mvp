import os

import asyncpg
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from queries import (
    get_calls_overview, get_calls_by_motive, get_calls_timeline,
    get_active_incidents, get_incident_zones,
    get_billing_summary, get_overdue_bills, get_active_expedients,
    get_work_orders_summary, get_recent_work_orders,
)

DATABASE_URL = os.getenv("DATABASE_URL", "")

app = FastAPI(title="EYD Dashboard")

pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


# ─── CALLS ───────────────────────────────────────────────

@app.get("/api/calls/overview")
async def calls_overview():
    async with pool.acquire() as conn:
        return await get_calls_overview(conn)


@app.get("/api/calls/motives")
async def calls_motives():
    async with pool.acquire() as conn:
        return await get_calls_by_motive(conn)


@app.get("/api/calls/timeline")
async def calls_timeline():
    async with pool.acquire() as conn:
        return await get_calls_timeline(conn)


# ─── INCIDENTS ───────────────────────────────────────────

@app.get("/api/incidents/active")
async def incidents_active():
    async with pool.acquire() as conn:
        return await get_active_incidents(conn)


@app.get("/api/incidents/zones")
async def incidents_zones():
    async with pool.acquire() as conn:
        return await get_incident_zones(conn)


# ─── BILLING ─────────────────────────────────────────────

@app.get("/api/billing/summary")
async def billing_summary():
    async with pool.acquire() as conn:
        return await get_billing_summary(conn)


@app.get("/api/billing/overdue")
async def billing_overdue():
    async with pool.acquire() as conn:
        return await get_overdue_bills(conn)


@app.get("/api/billing/expedients")
async def billing_expedients():
    async with pool.acquire() as conn:
        return await get_active_expedients(conn)


# ─── WORK ORDERS ─────────────────────────────────────────

@app.get("/api/work-orders/summary")
async def work_orders_summary():
    async with pool.acquire() as conn:
        return await get_work_orders_summary(conn)


@app.get("/api/work-orders/recent")
async def work_orders_recent():
    async with pool.acquire() as conn:
        return await get_recent_work_orders(conn)


# ─── STATIC FILES ────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")
