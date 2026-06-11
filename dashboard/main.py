import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import db
from routers import (
    abonados, analytics, contratos, direcciones, expedientes,
    facturacion, incidencias, llamadas, meta, partes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(db.connect_with_retries())
    logger.info("App started — DB connection running in background")
    yield
    task.cancel()
    await db.close_pool()


app = FastAPI(title="EYD Dashboard", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/health")
async def health():
    db_ok = False
    pool = db.get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_ok = True
        except Exception:
            pass
    return {"status": "ok", "db": db_ok}


# ─── API ROUTERS ─────────────────────────────────────────
for r in (analytics, abonados, direcciones, contratos, facturacion,
          expedientes, incidencias, partes, llamadas, meta):
    app.include_router(r.router)


# ─── STATIC FRONTEND ─────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")
