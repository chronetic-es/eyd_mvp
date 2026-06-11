"""Translate asyncpg constraint violations into friendly HTTP errors."""
from contextlib import asynccontextmanager

import asyncpg
from fastapi import HTTPException


@asynccontextmanager
async def db_errors(*, conflict_msg: str = "Operación en conflicto con datos existentes."):
    """Wrap DB writes; convert FK/unique violations into HTTP 409 with a clear message."""
    try:
        yield
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=409, detail=conflict_msg)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail=conflict_msg)
    except asyncpg.CheckViolationError as exc:
        raise HTTPException(status_code=400, detail=f"Datos no válidos: {exc}")
    except asyncpg.InvalidTextRepresentationError as exc:
        # e.g. a value outside an ENUM
        raise HTTPException(status_code=400, detail=f"Valor no permitido: {exc}")


def not_found(entity: str = "Registro"):
    raise HTTPException(status_code=404, detail=f"{entity} no encontrado.")
