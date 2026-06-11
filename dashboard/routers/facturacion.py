"""Recibos — CRUD + quick action 'marcar pagado'."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors, not_found
from models import ReciboIn, ReciboUpdate
from serializers import row, rows

router = APIRouter(prefix="/api/recibos", tags=["recibos"])


@router.get("")
async def list_recibos(estado: str = "", contrato_id: int | None = None, conn=Depends(get_conn)):
    clauses, args = [], []
    if estado:
        args.append(estado)
        clauses.append(f"hr.estado = ${len(args)}::estado_recibo")
    if contrato_id is not None:
        args.append(contrato_id)
        clauses.append(f"hr.contrato_id = ${len(args)}")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    data = await conn.fetch(f"""
        SELECT hr.id, hr.contrato_id, hr.periodo, hr.importe, hr.estado, hr.forma_pago,
               hr.fecha_emision, hr.fecha_vencimiento,
               c.numero_contrato, e.nombre, e.apellidos
        FROM historico_recibos hr
        JOIN contratos c ON hr.contrato_id = c.id
        JOIN entidades e ON c.entidad_id = e.id
        {where}
        ORDER BY hr.fecha_emision DESC
    """, *args)
    return {"recibos": rows(data)}


@router.post("", status_code=201)
async def create_recibo(body: ReciboIn, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="Contrato inexistente."):
        rec = await conn.fetchrow("""
            INSERT INTO historico_recibos
                (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *
        """, body.contrato_id, body.periodo, body.importe, body.estado,
            body.forma_pago, body.fecha_emision, body.fecha_vencimiento)
    return row(rec)


@router.put("/{recibo_id}")
async def update_recibo(recibo_id: int, body: ReciboUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "historico_recibos", recibo_id,
                            body.model_dump(exclude_unset=True), entity="Recibo")


@router.post("/{recibo_id}/marcar-pagado")
async def marcar_pagado(recibo_id: int, conn=Depends(get_conn)):
    rec = await conn.fetchrow(
        "UPDATE historico_recibos SET estado = 'Pagado' WHERE id = $1 RETURNING *", recibo_id)
    if not rec:
        not_found("Recibo")
    return row(rec)


@router.delete("/{recibo_id}", status_code=204)
async def delete_recibo(recibo_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "historico_recibos", recibo_id, entity="Recibo",
                      conflict_msg="No se puede borrar el recibo: está vinculado a un expediente de corte.")
