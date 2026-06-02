from instance import mcp
from db import obtener_conexion_db
from validators import formatear_precio


@mcp.tool()
async def consultar_recibos(contrato_id: int, solo_pendientes: bool = False) -> str:
    """Consulta el historico de recibos de un contrato. Si solo_pendientes es True,
    muestra unicamente los recibos pendientes, impagados o devueltos."""
    conn = await obtener_conexion_db()
    try:
        # Verify contract exists
        contrato = await conn.fetchrow(
            "SELECT numero_contrato FROM contratos WHERE id = $1",
            contrato_id,
        )
        if not contrato:
            return "No se ha encontrado ningun contrato con ese identificador."

        if solo_pendientes:
            recibos = await conn.fetch(
                """
                SELECT id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento
                FROM historico_recibos
                WHERE contrato_id = $1 AND estado IN ('Pendiente', 'Impagado', 'Devuelto')
                ORDER BY fecha_emision DESC
                """,
                contrato_id,
            )
        else:
            recibos = await conn.fetch(
                """
                SELECT id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento
                FROM historico_recibos
                WHERE contrato_id = $1
                ORDER BY fecha_emision DESC
                """,
                contrato_id,
            )

        if not recibos:
            if solo_pendientes:
                return f"El contrato {contrato['numero_contrato']} no tiene recibos pendientes. Todos al corriente de pago."
            return f"No se han encontrado recibos para el contrato {contrato['numero_contrato']}."

        partes = []
        for r in recibos:
            partes.append(
                f"Recibo periodo {r['periodo']}: {formatear_precio(float(r['importe']))}, "
                f"estado {r['estado']}, forma de pago {r['forma_pago']}, "
                f"emitido {r['fecha_emision']}, vencimiento {r['fecha_vencimiento']}"
            )

        tipo = "pendientes" if solo_pendientes else "en total"
        return (
            f"Contrato {contrato['numero_contrato']}: {len(recibos)} recibo{'s' if len(recibos) > 1 else ''} {tipo}. "
            + ". ".join(partes) + "."
        )
    except Exception:
        return "Error al consultar los recibos. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def consultar_estado_pagos(entidad_id: int) -> str:
    """Resumen de la situacion de pagos de un abonado en todos sus contratos:
    recibos pendientes, deuda total y expedientes de corte activos."""
    conn = await obtener_conexion_db()
    try:
        entidad = await conn.fetchrow(
            "SELECT nombre, apellidos FROM entidades WHERE id = $1",
            entidad_id,
        )
        if not entidad:
            return "No se ha encontrado ningun abonado con ese identificador."

        # Pending bills across all contracts
        pendientes = await conn.fetch(
            """
            SELECT c.numero_contrato, hr.periodo, hr.importe, hr.estado, hr.fecha_vencimiento
            FROM historico_recibos hr
            JOIN contratos c ON hr.contrato_id = c.id
            WHERE c.entidad_id = $1 AND hr.estado IN ('Pendiente', 'Impagado', 'Devuelto')
            ORDER BY hr.fecha_vencimiento
            """,
            entidad_id,
        )

        # Active cut expedients
        expedientes = await conn.fetch(
            """
            SELECT c.numero_contrato, ec.estado, ec.fecha_apertura, ec.fecha_corte, ec.importe_deuda
            FROM expedientes_corte ec
            JOIN contratos c ON ec.contrato_id = c.id
            WHERE c.entidad_id = $1 AND ec.estado NOT IN ('Cerrado')
            ORDER BY ec.fecha_apertura
            """,
            entidad_id,
        )

        resultado = [f"Resumen de pagos de {entidad['nombre']} {entidad['apellidos']}."]

        if pendientes:
            deuda_total = sum(float(p["importe"]) for p in pendientes)
            resultado.append(
                f"Tiene {len(pendientes)} recibo{'s' if len(pendientes) > 1 else ''} "
                f"pendiente{'s' if len(pendientes) > 1 else ''} de pago, "
                f"por un total de {formatear_precio(deuda_total)}."
            )
            for p in pendientes:
                resultado.append(
                    f"Contrato {p['numero_contrato']}, periodo {p['periodo']}: "
                    f"{formatear_precio(float(p['importe']))}, estado {p['estado']}, "
                    f"vencimiento {p['fecha_vencimiento']}"
                )
        else:
            resultado.append("No tiene recibos pendientes. Todos los pagos al corriente.")

        if expedientes:
            resultado.append(
                f"ATENCION: Tiene {len(expedientes)} expediente{'s' if len(expedientes) > 1 else ''} de corte activo{'s' if len(expedientes) > 1 else ''}."
            )
            for e in expedientes:
                deuda = formatear_precio(float(e["importe_deuda"])) if e["importe_deuda"] else "sin importe registrado"
                corte = f", corte previsto {e['fecha_corte']}" if e["fecha_corte"] else ""
                resultado.append(
                    f"Contrato {e['numero_contrato']}: expediente {e['estado']}, "
                    f"abierto {e['fecha_apertura']}{corte}. Deuda: {deuda}"
                )

        return " ".join(resultado)
    except Exception:
        return "Error al consultar el estado de pagos. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def consultar_expediente_corte(contrato_id: int) -> str:
    """Consulta los expedientes de corte para un contrato, con su estado,
    fechas clave e importe de deuda."""
    conn = await obtener_conexion_db()
    try:
        contrato = await conn.fetchrow(
            "SELECT numero_contrato FROM contratos WHERE id = $1",
            contrato_id,
        )
        if not contrato:
            return "No se ha encontrado ningun contrato con ese identificador."

        expedientes = await conn.fetch(
            """
            SELECT id, estado, fecha_apertura, fecha_corte, importe_deuda
            FROM expedientes_corte
            WHERE contrato_id = $1
            ORDER BY fecha_apertura DESC
            """,
            contrato_id,
        )

        if not expedientes:
            return f"El contrato {contrato['numero_contrato']} no tiene expedientes de corte."

        partes = []
        for e in expedientes:
            deuda = formatear_precio(float(e["importe_deuda"])) if e["importe_deuda"] else "sin importe registrado"
            corte = f", fecha de corte: {e['fecha_corte']}" if e["fecha_corte"] else ""
            partes.append(
                f"Expediente ID {e['id']}: estado {e['estado']}, "
                f"abierto el {e['fecha_apertura']}{corte}. Deuda: {deuda}"
            )

        return (
            f"Contrato {contrato['numero_contrato']}: "
            f"{len(expedientes)} expediente{'s' if len(expedientes) > 1 else ''} de corte. "
            + ". ".join(partes) + "."
        )
    except Exception:
        return "Error al consultar los expedientes de corte. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
