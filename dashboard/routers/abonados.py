"""Abonados (entidades) — CRUD + 360 view."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors, not_found
from models import AbonadoIn, AbonadoUpdate
from serializers import row, rows

router = APIRouter(prefix="/api/abonados", tags=["abonados"])


@router.get("")
async def list_abonados(search: str = "", conn=Depends(get_conn)):
    if search:
        like = f"%{search}%"
        data = await conn.fetch("""
            SELECT e.id, e.nif, e.nombre, e.apellidos, e.telefono, e.dir_fiscal,
                   COUNT(c.id) AS num_contratos
            FROM entidades e
            LEFT JOIN contratos c ON c.entidad_id = e.id
            WHERE e.nif ILIKE $1 OR e.nombre ILIKE $1 OR e.apellidos ILIKE $1 OR e.telefono ILIKE $1
            GROUP BY e.id
            ORDER BY e.apellidos, e.nombre
        """, like)
    else:
        data = await conn.fetch("""
            SELECT e.id, e.nif, e.nombre, e.apellidos, e.telefono, e.dir_fiscal,
                   COUNT(c.id) AS num_contratos
            FROM entidades e
            LEFT JOIN contratos c ON c.entidad_id = e.id
            GROUP BY e.id
            ORDER BY e.apellidos, e.nombre
        """)
    return {"abonados": rows(data)}


@router.get("/{abonado_id}")
async def get_abonado(abonado_id: int, conn=Depends(get_conn)):
    ent = await conn.fetchrow("SELECT * FROM entidades WHERE id = $1", abonado_id)
    if not ent:
        not_found("Abonado")

    contratos = await conn.fetch("""
        SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta, c.fecha_baja,
               d.id AS direccion_id, d.calle, d.numero, d.portal, d.planta, d.letra,
               d.cod_postal, d.municipio
        FROM contratos c
        JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
        WHERE c.entidad_id = $1
        ORDER BY c.fecha_alta DESC
    """, abonado_id)

    result_contratos = []
    for c in contratos:
        contadores = await conn.fetch("""
            SELECT id, num_serie, fecha_alta, fecha_baja, lectura_m3, fecha_lectura
            FROM contadores WHERE contrato_id = $1 ORDER BY fecha_lectura DESC
        """, c["id"])
        recibos = await conn.fetch("""
            SELECT id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento
            FROM historico_recibos WHERE contrato_id = $1 ORDER BY fecha_emision DESC
        """, c["id"])
        expedientes = await conn.fetch("""
            SELECT id, estado, fecha_apertura, fecha_corte, importe_deuda
            FROM expedientes_corte WHERE contrato_id = $1 ORDER BY fecha_apertura DESC
        """, c["id"])
        result_contratos.append({
            **row(c),
            "contadores": rows(contadores),
            "recibos": rows(recibos),
            "expedientes": rows(expedientes),
        })

    llamadas = await conn.fetch("""
        SELECT id, fecha_inicio, fecha_fin, motivo_detectado, estado, human_handoff, resumen_ia
        FROM llamadas WHERE telefono = $1 ORDER BY fecha_inicio DESC
    """, ent["telefono"])

    return {
        "abonado": row(ent),
        "contratos": result_contratos,
        "llamadas": rows(llamadas),
    }


@router.post("", status_code=201)
async def create_abonado(body: AbonadoIn, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="Ya existe un abonado con ese NIF."):
        rec = await conn.fetchrow("""
            INSERT INTO entidades (nif, nombre, apellidos, telefono, dir_fiscal)
            VALUES ($1, $2, $3, $4, $5) RETURNING *
        """, body.nif, body.nombre, body.apellidos, body.telefono, body.dir_fiscal)
    return row(rec)


@router.put("/{abonado_id}")
async def update_abonado(abonado_id: int, body: AbonadoUpdate, conn=Depends(get_conn)):
    return await crud.patch(
        conn, "entidades", abonado_id, body.model_dump(exclude_unset=True),
        entity="Abonado", conflict_msg="Ya existe un abonado con ese NIF.",
    )


@router.delete("/{abonado_id}", status_code=204)
async def delete_abonado(abonado_id: int, conn=Depends(get_conn)):
    await crud.delete(
        conn, "entidades", abonado_id,
        entity="Abonado", conflict_msg="No se puede borrar el abonado: tiene contratos asociados.",
    )
