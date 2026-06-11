"""Generic helpers for partial updates and deletes.

Table names passed here are hardcoded constants inside routers (never user
input), so direct interpolation into SQL is safe.
"""
from errors import db_errors, not_found
from serializers import row


async def fetch_one(conn, table: str, id_: int):
    return await conn.fetchrow(f"SELECT * FROM {table} WHERE id = $1", id_)


async def patch(conn, table: str, id_: int, fields: dict, *,
                entity: str = "Registro", conflict_msg: str = "Conflicto con datos existentes."):
    """Apply a partial UPDATE with only the provided fields; returns the updated row."""
    if not fields:
        rec = await fetch_one(conn, table, id_)
        if not rec:
            not_found(entity)
        return row(rec)
    sets = ", ".join(f"{k} = ${i}" for i, k in enumerate(fields, start=2))
    async with db_errors(conflict_msg=conflict_msg):
        rec = await conn.fetchrow(
            f"UPDATE {table} SET {sets} WHERE id = $1 RETURNING *",
            id_, *fields.values(),
        )
    if not rec:
        not_found(entity)
    return row(rec)


async def delete(conn, table: str, id_: int, *,
                 entity: str = "Registro", conflict_msg: str = "No se puede borrar: tiene datos asociados."):
    async with db_errors(conflict_msg=conflict_msg):
        result = await conn.execute(f"DELETE FROM {table} WHERE id = $1", id_)
    if result == "DELETE 0":
        not_found(entity)
