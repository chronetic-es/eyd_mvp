"""Incidencias — CRUD + manage affected addresses + nested work orders."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors, not_found
from models import DireccionLink, IncidenciaIn, IncidenciaUpdate, ZonaLink
from serializers import row, rows

router = APIRouter(prefix="/api/incidencias", tags=["incidencias"])

# Canonical "address falls within incident" rule, reused for the affected-subscribers query.
# Params: $1 = incidencia_id. Joins against a supply address aliased `d`.
_ZONA_MATCH = """
    d.id IN (SELECT direccion_suministro_id FROM incidencia_direcciones WHERE incidencia_id = $1)
    OR EXISTS (
        SELECT 1 FROM incidencia_zonas iz WHERE iz.incidencia_id = $1 AND (
            (iz.ambito = 'Calle'
                AND LOWER(TRIM(d.calle)) = LOWER(TRIM(iz.valor))
                AND (iz.municipio IS NULL OR LOWER(iz.municipio) = LOWER(d.municipio)))
            OR (iz.ambito = 'Codigo_postal' AND d.cod_postal = iz.valor)
            OR (iz.ambito = 'Municipio' AND LOWER(iz.valor) = LOWER(d.municipio))
        )
    )
"""


async def _with_relations(conn, inc) -> dict:
    addresses = await conn.fetch("""
        SELECT d.id, d.calle, d.numero, d.cod_postal, d.municipio
        FROM incidencia_direcciones idl
        JOIN direcciones_suministro d ON idl.direccion_suministro_id = d.id
        WHERE idl.incidencia_id = $1
    """, inc["id"])
    zones = await conn.fetch("""
        SELECT id, ambito, valor, municipio
        FROM incidencia_zonas WHERE incidencia_id = $1 ORDER BY id
    """, inc["id"])
    work_orders = await conn.fetch("""
        SELECT id, numero_parte, estado, fecha, descripcion
        FROM partes_trabajo WHERE incidencia_id = $1 ORDER BY fecha DESC
    """, inc["id"])
    return {
        **row(inc),
        "active": inc["fecha_fin"] is None,
        "addresses": rows(addresses),
        "zones": rows(zones),
        "work_orders": rows(work_orders),
    }


@router.get("")
async def list_incidencias(conn=Depends(get_conn)):
    incidents = await conn.fetch("""
        SELECT * FROM incidencias
        ORDER BY fecha_fin NULLS FIRST, fecha_inicio DESC
    """)
    result = [await _with_relations(conn, inc) for inc in incidents]
    active_count = sum(1 for i in result if i["active"])
    return {"incidents": result, "active_count": active_count, "total_count": len(result)}


@router.get("/{incidencia_id}")
async def get_incidencia(incidencia_id: int, conn=Depends(get_conn)):
    inc = await conn.fetchrow("SELECT * FROM incidencias WHERE id = $1", incidencia_id)
    if not inc:
        not_found("Incidencia")
    return await _with_relations(conn, inc)


@router.post("", status_code=201)
async def create_incidencia(body: IncidenciaIn, conn=Depends(get_conn)):
    rec = await conn.fetchrow("""
        INSERT INTO incidencias
            (tipo, fecha_inicio, hora_inicio, fecha_fin, hora_fin,
             fecha_fin_prevista, hora_fin_prevista, descripcion)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *
    """, body.tipo, body.fecha_inicio, body.hora_inicio, body.fecha_fin, body.hora_fin,
        body.fecha_fin_prevista, body.hora_fin_prevista, body.descripcion)
    return await _with_relations(conn, rec)


@router.put("/{incidencia_id}")
async def update_incidencia(incidencia_id: int, body: IncidenciaUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "incidencias", incidencia_id,
                            body.model_dump(exclude_unset=True), entity="Incidencia")


@router.delete("/{incidencia_id}", status_code=204)
async def delete_incidencia(incidencia_id: int, conn=Depends(get_conn)):
    # incidencia_direcciones cascades; partes_trabajo.incidencia_id is nullable FK → may block.
    await crud.delete(conn, "incidencias", incidencia_id, entity="Incidencia",
                      conflict_msg="No se puede borrar la incidencia: tiene partes de trabajo asociados.")


# ─── Affected addresses (N:M) ────────────────────────────

@router.post("/{incidencia_id}/direcciones", status_code=201)
async def link_direccion(incidencia_id: int, body: DireccionLink, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="La dirección ya está enlazada o no existe."):
        await conn.execute("""
            INSERT INTO incidencia_direcciones (incidencia_id, direccion_suministro_id)
            VALUES ($1, $2)
        """, incidencia_id, body.direccion_suministro_id)
    inc = await conn.fetchrow("SELECT * FROM incidencias WHERE id = $1", incidencia_id)
    return await _with_relations(conn, inc)


@router.delete("/{incidencia_id}/direcciones/{direccion_id}", status_code=204)
async def unlink_direccion(incidencia_id: int, direccion_id: int, conn=Depends(get_conn)):
    result = await conn.execute("""
        DELETE FROM incidencia_direcciones
        WHERE incidencia_id = $1 AND direccion_suministro_id = $2
    """, incidencia_id, direccion_id)
    if result == "DELETE 0":
        not_found("Enlace")


# ─── Affected zones (general scope) ──────────────────────

@router.post("/{incidencia_id}/zonas", status_code=201)
async def add_zona(incidencia_id: int, body: ZonaLink, conn=Depends(get_conn)):
    municipio = body.municipio if body.ambito == "Calle" else None
    async with db_errors(conflict_msg="Incidencia inexistente."):
        await conn.execute("""
            INSERT INTO incidencia_zonas (incidencia_id, ambito, valor, municipio)
            VALUES ($1, $2, $3, $4)
        """, incidencia_id, body.ambito, body.valor, municipio)
    inc = await conn.fetchrow("SELECT * FROM incidencias WHERE id = $1", incidencia_id)
    return await _with_relations(conn, inc)


@router.delete("/{incidencia_id}/zonas/{zona_id}", status_code=204)
async def remove_zona(incidencia_id: int, zona_id: int, conn=Depends(get_conn)):
    result = await conn.execute(
        "DELETE FROM incidencia_zonas WHERE id = $1 AND incidencia_id = $2",
        zona_id, incidencia_id,
    )
    if result == "DELETE 0":
        not_found("Zona")


# ─── Affected subscribers (exact links + zone matching) ──

@router.get("/{incidencia_id}/afectados")
async def get_afectados(incidencia_id: int, conn=Depends(get_conn)):
    if not await conn.fetchrow("SELECT 1 FROM incidencias WHERE id = $1", incidencia_id):
        not_found("Incidencia")
    afectados = await conn.fetch(f"""
        SELECT DISTINCT c.id AS contrato_id, c.numero_contrato, c.estado AS estado_contrato,
               e.id AS abonado_id, e.nombre, e.apellidos, e.telefono,
               d.calle, d.numero, d.cod_postal, d.municipio
        FROM contratos c
        JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
        JOIN entidades e ON c.entidad_id = e.id
        WHERE {_ZONA_MATCH}
        ORDER BY e.apellidos, e.nombre
    """, incidencia_id)
    return {"afectados": rows(afectados), "total": len(afectados)}
