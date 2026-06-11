"""Expedientes de corte — CRUD."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors
from models import ExpedienteIn, ExpedienteUpdate
from serializers import row, rows

router = APIRouter(prefix="/api/expedientes", tags=["expedientes"])


@router.get("")
async def list_expedientes(estado: str = "", conn=Depends(get_conn)):
    clause = "WHERE ec.estado = $1::estado_expediente" if estado else ""
    args = [estado] if estado else []
    data = await conn.fetch(f"""
        SELECT ec.id, ec.contrato_id, ec.recibo_id, ec.fecha_apertura, ec.fecha_corte,
               ec.estado, ec.importe_deuda,
               c.numero_contrato, e.nombre, e.apellidos
        FROM expedientes_corte ec
        JOIN contratos c ON ec.contrato_id = c.id
        JOIN entidades e ON c.entidad_id = e.id
        {clause}
        ORDER BY ec.fecha_apertura DESC
    """, *args)
    return {"expedientes": rows(data)}


@router.post("", status_code=201)
async def create_expediente(body: ExpedienteIn, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="Contrato o recibo inexistente."):
        rec = await conn.fetchrow("""
            INSERT INTO expedientes_corte
                (contrato_id, recibo_id, fecha_apertura, fecha_corte, estado, importe_deuda)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING *
        """, body.contrato_id, body.recibo_id, body.fecha_apertura, body.fecha_corte,
            body.estado, body.importe_deuda)
    return row(rec)


@router.put("/{expediente_id}")
async def update_expediente(expediente_id: int, body: ExpedienteUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "expedientes_corte", expediente_id,
                            body.model_dump(exclude_unset=True), entity="Expediente")


@router.delete("/{expediente_id}", status_code=204)
async def delete_expediente(expediente_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "expedientes_corte", expediente_id, entity="Expediente")
