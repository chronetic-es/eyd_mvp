"""Read-only analytics endpoints — power the dashboard charts/KPIs.

These preserve the original /api/calls, /api/incidents, /api/billing,
/api/work-orders routes so existing views keep working unchanged.
"""
from fastapi import APIRouter, Depends

from db import get_conn
from serializers import row, rows

router = APIRouter(prefix="/api", tags=["analytics"])


# ─── GLOBAL SUMMARY (Resumen tab) ────────────────────────

@router.get("/summary")
async def global_summary(conn=Depends(get_conn)):
    stats = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM entidades) AS abonados,
            (SELECT COUNT(*) FROM contratos WHERE estado = 'Activo') AS contratos_activos,
            (SELECT COUNT(*) FROM incidencias WHERE fecha_fin IS NULL) AS incidencias_activas,
            (SELECT COUNT(*) FROM partes_trabajo WHERE estado != 'Cerrado') AS partes_abiertos,
            (SELECT COUNT(*) FROM llamadas WHERE fecha_inicio >= CURRENT_DATE - INTERVAL '7 days') AS llamadas_7d,
            (SELECT COALESCE(SUM(importe_deuda), 0) FROM expedientes_corte WHERE estado != 'Cerrado') AS deuda_activa,
            (SELECT COUNT(*) FROM historico_recibos WHERE estado IN ('Impagado', 'Devuelto')) AS recibos_impagados
    """)
    return row(stats)


# ─── CALLS ───────────────────────────────────────────────

@router.get("/calls/overview")
async def calls_overview(conn=Depends(get_conn)):
    stats = await conn.fetchrow("""
        SELECT
            COUNT(*) AS total_calls,
            COUNT(*) FILTER (WHERE estado = 'Escalada') AS escalated,
            COUNT(*) FILTER (WHERE human_handoff = TRUE) AS handoffs,
            COUNT(*) FILTER (WHERE fecha_inicio >= CURRENT_DATE - INTERVAL '7 days') AS last_7_days
        FROM llamadas
    """)
    calls = await conn.fetch("""
        SELECT l.id, l.telefono, l.fecha_inicio, l.fecha_fin,
               l.motivo_detectado, l.estado, l.human_handoff, l.resumen_ia,
               e.nombre, e.apellidos
        FROM llamadas l
        LEFT JOIN entidades e ON l.telefono = e.telefono
        ORDER BY l.fecha_inicio DESC
        LIMIT 50
    """)
    total = stats["total_calls"] or 0
    escalated = stats["escalated"] or 0
    return {
        "total_calls": total,
        "escalated": escalated,
        "escalation_rate": round(escalated / total * 100, 1) if total > 0 else 0,
        "handoffs": stats["handoffs"] or 0,
        "last_7_days": stats["last_7_days"] or 0,
        "calls": rows(calls),
    }


@router.get("/calls/motives")
async def calls_motives(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT motivo_detectado AS motive, COUNT(*) AS count
        FROM llamadas
        WHERE motivo_detectado IS NOT NULL
        GROUP BY motivo_detectado
        ORDER BY count DESC
    """)
    return {"motives": rows(data)}


@router.get("/calls/timeline")
async def calls_timeline(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT fecha_inicio::date AS date, COUNT(*) AS count
        FROM llamadas
        WHERE fecha_inicio >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY fecha_inicio::date
        ORDER BY date
    """)
    return {"timeline": [{"date": str(r["date"]), "count": r["count"]} for r in data]}


# ─── INCIDENTS ───────────────────────────────────────────

@router.get("/incidents/active")
async def incidents_active(conn=Depends(get_conn)):
    incidents = await conn.fetch("""
        SELECT id, tipo, descripcion, fecha_inicio, hora_inicio,
               fecha_fin, hora_fin, fecha_fin_prevista, hora_fin_prevista
        FROM incidencias
        ORDER BY fecha_fin NULLS FIRST, fecha_inicio DESC
    """)
    result = []
    for inc in incidents:
        addresses = await conn.fetch("""
            SELECT d.calle, d.numero, d.cod_postal, d.municipio
            FROM incidencia_direcciones idl
            JOIN direcciones_suministro d ON idl.direccion_suministro_id = d.id
            WHERE idl.incidencia_id = $1
        """, inc["id"])
        work_orders = await conn.fetch("""
            SELECT numero_parte, estado, fecha, descripcion
            FROM partes_trabajo
            WHERE incidencia_id = $1
            ORDER BY fecha DESC
        """, inc["id"])
        result.append({
            **row(inc),
            "active": inc["fecha_fin"] is None,
            "addresses": rows(addresses),
            "work_orders": rows(work_orders),
        })
    active_count = sum(1 for i in result if i["active"])
    return {"incidents": result, "active_count": active_count, "total_count": len(result)}


@router.get("/incidents/zones")
async def incident_zones(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT d.municipio AS zone, COUNT(DISTINCT i.id) AS incident_count
        FROM incidencias i
        JOIN incidencia_direcciones idl ON i.id = idl.incidencia_id
        JOIN direcciones_suministro d ON idl.direccion_suministro_id = d.id
        WHERE i.fecha_fin IS NULL
        GROUP BY d.municipio
        ORDER BY incident_count DESC
    """)
    return {"zones": rows(data)}


# ─── BILLING ─────────────────────────────────────────────

@router.get("/billing/summary")
async def billing_summary(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT estado AS status, COUNT(*) AS count, COALESCE(SUM(importe), 0) AS total_amount
        FROM historico_recibos
        GROUP BY estado
        ORDER BY count DESC
    """)
    total_bills = sum(r["count"] for r in data)
    total_revenue = sum(float(r["total_amount"]) for r in data)
    overdue = await conn.fetchrow("""
        SELECT COUNT(*) AS count, COALESCE(SUM(importe), 0) AS total
        FROM historico_recibos
        WHERE estado IN ('Impagado', 'Devuelto', 'Pendiente')
          AND fecha_vencimiento < CURRENT_DATE
    """)
    return {
        "by_status": [
            {"status": r["status"], "count": r["count"], "amount": float(r["total_amount"])}
            for r in data
        ],
        "total_bills": total_bills,
        "total_revenue": round(total_revenue, 2),
        "overdue_count": overdue["count"] or 0,
        "overdue_amount": float(overdue["total"] or 0),
    }


@router.get("/billing/overdue")
async def billing_overdue(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT hr.id, hr.periodo, hr.importe, hr.estado, hr.fecha_emision,
               hr.fecha_vencimiento, hr.forma_pago,
               c.numero_contrato,
               e.nombre, e.apellidos, e.telefono
        FROM historico_recibos hr
        JOIN contratos c ON hr.contrato_id = c.id
        JOIN entidades e ON c.entidad_id = e.id
        WHERE hr.estado IN ('Impagado', 'Devuelto', 'Pendiente')
        ORDER BY hr.fecha_vencimiento ASC
    """)
    return {"overdue_bills": rows(data)}


@router.get("/billing/expedients")
async def billing_expedients(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT ec.id, ec.estado, ec.fecha_apertura, ec.fecha_corte, ec.importe_deuda,
               c.numero_contrato,
               e.nombre, e.apellidos, e.telefono
        FROM expedientes_corte ec
        JOIN contratos c ON ec.contrato_id = c.id
        JOIN entidades e ON c.entidad_id = e.id
        WHERE ec.estado != 'Cerrado'
        ORDER BY ec.fecha_apertura
    """)
    total_debt = sum(float(r["importe_deuda"] or 0) for r in data)
    return {"expedients": rows(data), "active_count": len(data), "total_debt": round(total_debt, 2)}


# ─── WORK ORDERS ─────────────────────────────────────────

@router.get("/work-orders/summary")
async def work_orders_summary(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT estado AS status, COUNT(*) AS count
        FROM partes_trabajo
        GROUP BY estado
        ORDER BY count DESC
    """)
    return {"by_status": rows(data), "total": sum(r["count"] for r in data)}


@router.get("/work-orders/recent")
async def work_orders_recent(conn=Depends(get_conn)):
    data = await conn.fetch("""
        SELECT pt.id, pt.numero_parte, pt.estado, pt.fecha, pt.descripcion,
               d.calle, d.numero, d.municipio,
               i.tipo AS incident_type, i.id AS incident_id
        FROM partes_trabajo pt
        LEFT JOIN direcciones_suministro d ON pt.direccion_suministro_id = d.id
        LEFT JOIN incidencias i ON pt.incidencia_id = i.id
        ORDER BY pt.fecha DESC
        LIMIT 20
    """)
    return {"work_orders": rows(data)}
