"""Partes de trabajo — CRUD with auto-generated numero_parte (PT-YYYY-NNNN)."""
import datetime

from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors
from models import ParteIn, ParteUpdate
from serializers import row, rows

router = APIRouter(prefix="/api/partes", tags=["partes"])


@router.get("")
async def list_partes(estado: str = "", incidencia_id: int | None = None, conn=Depends(get_conn)):
    clauses, args = [], []
    if estado:
        args.append(estado)
        clauses.append(f"pt.estado = ${len(args)}::estado_parte")
    if incidencia_id is not None:
        args.append(incidencia_id)
        clauses.append(f"pt.incidencia_id = ${len(args)}")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    data = await conn.fetch(f"""
        SELECT pt.id, pt.numero_parte, pt.estado, pt.fecha, pt.descripcion,
               pt.direccion_suministro_id, pt.incidencia_id,
               d.calle, d.numero, d.municipio,
               i.tipo AS incident_type
        FROM partes_trabajo pt
        LEFT JOIN direcciones_suministro d ON pt.direccion_suministro_id = d.id
        LEFT JOIN incidencias i ON pt.incidencia_id = i.id
        {where}
        ORDER BY pt.fecha DESC, pt.id DESC
    """, *args)
    return {"partes": rows(data)}


@router.post("", status_code=201)
async def create_parte(body: ParteIn, conn=Depends(get_conn)):
    # Auto-generate numero_parte PT-YYYY-NNNN from the next sequence value.
    next_id = await conn.fetchval("SELECT COALESCE(MAX(id), 0) + 1 FROM partes_trabajo")
    numero_parte = f"PT-{datetime.date.today().year}-{next_id:04d}"
    fecha = body.fecha or datetime.date.today()
    async with db_errors(conflict_msg="Dirección o incidencia inexistente, o número de parte duplicado."):
        rec = await conn.fetchrow("""
            INSERT INTO partes_trabajo
                (numero_parte, direccion_suministro_id, incidencia_id, fecha, estado, descripcion)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING *
        """, numero_parte, body.direccion_suministro_id, body.incidencia_id,
            fecha, body.estado, body.descripcion)
    return row(rec)


@router.put("/{parte_id}")
async def update_parte(parte_id: int, body: ParteUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "partes_trabajo", parte_id,
                            body.model_dump(exclude_unset=True), entity="Parte")


@router.delete("/{parte_id}", status_code=204)
async def delete_parte(parte_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "partes_trabajo", parte_id, entity="Parte")
