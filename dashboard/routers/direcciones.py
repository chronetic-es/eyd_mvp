"""Direcciones de suministro — CRUD."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors
from models import DireccionIn, DireccionUpdate
from serializers import row, rows

router = APIRouter(prefix="/api/direcciones", tags=["direcciones"])


@router.get("")
async def list_direcciones(search: str = "", conn=Depends(get_conn)):
    if search:
        like = f"%{search}%"
        data = await conn.fetch("""
            SELECT * FROM direcciones_suministro
            WHERE calle ILIKE $1 OR municipio ILIKE $1 OR cod_postal ILIKE $1
            ORDER BY municipio, calle
        """, like)
    else:
        data = await conn.fetch(
            "SELECT * FROM direcciones_suministro ORDER BY municipio, calle")
    return {"direcciones": rows(data)}


@router.post("", status_code=201)
async def create_direccion(body: DireccionIn, conn=Depends(get_conn)):
    async with db_errors():
        rec = await conn.fetchrow("""
            INSERT INTO direcciones_suministro
                (calle, numero, portal, planta, letra, cod_postal, municipio)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *
        """, body.calle, body.numero, body.portal, body.planta, body.letra,
            body.cod_postal, body.municipio)
    return row(rec)


@router.put("/{direccion_id}")
async def update_direccion(direccion_id: int, body: DireccionUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "direcciones_suministro", direccion_id,
                            body.model_dump(exclude_unset=True), entity="Dirección")


@router.delete("/{direccion_id}", status_code=204)
async def delete_direccion(direccion_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "direcciones_suministro", direccion_id, entity="Dirección",
                      conflict_msg="No se puede borrar la dirección: está en uso por contratos, incidencias o partes.")
