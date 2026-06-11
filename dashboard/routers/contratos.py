"""Contratos — CRUD, plus nested contadores (meter readings)."""
from fastapi import APIRouter, Depends

import crud
from db import get_conn
from errors import db_errors
from models import ContadorIn, ContadorUpdate, ContratoIn, ContratoUpdate
from serializers import row, rows

router = APIRouter(prefix="/api", tags=["contratos"])


# ─── CONTRATOS ───────────────────────────────────────────

@router.get("/contratos")
async def list_contratos(search: str = "", entidad_id: int | None = None, conn=Depends(get_conn)):
    clauses, args = [], []
    if entidad_id is not None:
        args.append(entidad_id)
        clauses.append(f"c.entidad_id = ${len(args)}")
    if search:
        args.append(f"%{search}%")
        clauses.append(f"(c.numero_contrato ILIKE ${len(args)} OR e.nombre ILIKE ${len(args)} OR e.apellidos ILIKE ${len(args)})")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    data = await conn.fetch(f"""
        SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta, c.fecha_baja,
               c.entidad_id, c.direccion_suministro_id,
               e.nombre, e.apellidos, e.nif,
               d.calle, d.numero, d.municipio
        FROM contratos c
        JOIN entidades e ON c.entidad_id = e.id
        JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
        {where}
        ORDER BY c.fecha_alta DESC
    """, *args)
    return {"contratos": rows(data)}


@router.post("/contratos", status_code=201)
async def create_contrato(body: ContratoIn, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="Número de contrato duplicado, o abonado/dirección inexistente."):
        rec = await conn.fetchrow("""
            INSERT INTO contratos
                (numero_contrato, entidad_id, direccion_suministro_id, estado, fecha_alta, fecha_baja)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING *
        """, body.numero_contrato, body.entidad_id, body.direccion_suministro_id,
            body.estado, body.fecha_alta, body.fecha_baja)
    return row(rec)


@router.put("/contratos/{contrato_id}")
async def update_contrato(contrato_id: int, body: ContratoUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "contratos", contrato_id, body.model_dump(exclude_unset=True),
                            entity="Contrato", conflict_msg="Número de contrato duplicado.")


@router.delete("/contratos/{contrato_id}", status_code=204)
async def delete_contrato(contrato_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "contratos", contrato_id, entity="Contrato",
                      conflict_msg="No se puede borrar el contrato: tiene recibos, contadores o expedientes asociados.")


# ─── CONTADORES (nested) ─────────────────────────────────

@router.get("/contratos/{contrato_id}/contadores")
async def list_contadores(contrato_id: int, conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT id, contrato_id, num_serie, fecha_alta, fecha_baja, lectura_m3, fecha_lectura
        FROM contadores WHERE contrato_id = $1 ORDER BY fecha_lectura DESC
    """, contrato_id)
    return {"contadores": rows(data)}


@router.post("/contadores", status_code=201)
async def create_contador(body: ContadorIn, conn=Depends(get_conn)):
    async with db_errors(conflict_msg="Contrato inexistente."):
        rec = await conn.fetchrow("""
            INSERT INTO contadores
                (contrato_id, num_serie, fecha_alta, fecha_baja, lectura_m3, fecha_lectura)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING *
        """, body.contrato_id, body.num_serie, body.fecha_alta, body.fecha_baja,
            body.lectura_m3, body.fecha_lectura)
    return row(rec)


@router.put("/contadores/{contador_id}")
async def update_contador(contador_id: int, body: ContadorUpdate, conn=Depends(get_conn)):
    return await crud.patch(conn, "contadores", contador_id, body.model_dump(exclude_unset=True),
                            entity="Contador")


@router.delete("/contadores/{contador_id}", status_code=204)
async def delete_contador(contador_id: int, conn=Depends(get_conn)):
    await crud.delete(conn, "contadores", contador_id, entity="Contador")
