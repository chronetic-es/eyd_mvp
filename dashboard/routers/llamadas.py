"""Llamadas — list (extended), update, delete. (Creation is done by Marina/MCP.)"""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from models import LlamadaUpdate
from serializers import rows

router = APIRouter(prefix="/api/llamadas", tags=["llamadas"])


@router.get("")
async def list_llamadas(search: str = "", conn=Depends(get_conn)):
    if search:
        like = f"%{search}%"
        data = await conn.fetch("""
            SELECT l.id, l.telefono, l.fecha_inicio, l.fecha_fin, l.transcripcion,
                   l.resumen_ia, l.motivo_detectado, l.human_handoff, l.estado,
                   e.nombre, e.apellidos
            FROM llamadas l
            LEFT JOIN entidades e ON l.telefono = e.telefono
            WHERE l.telefono ILIKE $1 OR l.resumen_ia ILIKE $1
               OR e.nombre ILIKE $1 OR e.apellidos ILIKE $1
            ORDER BY l.fecha_inicio DESC
        """, like)
    else:
        data = await conn.fetch("""
            SELECT l.id, l.telefono, l.fecha_inicio, l.fecha_fin, l.transcripcion,
                   l.resumen_ia, l.motivo_detectado, l.human_handoff, l.estado,
                   e.nombre, e.apellidos
            FROM llamadas l
            LEFT JOIN entidades e ON l.telefono = e.telefono
            ORDER BY l.fecha_inicio DESC
        """)
    return {"llamadas": rows(data)}


@router.put("/{llamada_id}")
async def update_llamada(llamada_id: int, body: LlamadaUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "llamadas", llamada_id,
                            body.model_dump(exclude_unset=True), entity="Llamada")


@router.delete("/{llamada_id}", status_code=204)
async def delete_llamada(llamada_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "llamadas", llamada_id, entity="Llamada")
