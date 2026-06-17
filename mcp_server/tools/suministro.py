from instance import mcp
from db import obtener_conexion_db
from validators import formatear_precio


@mcp.tool()
async def verificar_estado_suministro(contrato_id: int) -> str:
    """Verifica el estado actual del suministro para un contrato: estado del contrato,
    incidencias activas en la zona, expedientes de corte abiertos y ultima lectura del contador.
    Devuelve un resumen completo del estado del suministro. Usa esta herramienta cuando un
    abonado reporta falta de agua o problemas con su suministro."""
    conn = await obtener_conexion_db()
    try:
        # 1. Contract info
        contrato = await conn.fetchrow(
            """
            SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta,
                   d.id AS dir_id, d.calle, d.numero, d.portal, d.planta, d.letra,
                   d.cod_postal, d.municipio,
                   e.nombre, e.apellidos
            FROM contratos c
            JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
            JOIN entidades e ON c.entidad_id = e.id
            WHERE c.id = $1
            """,
            contrato_id,
        )
        if not contrato:
            return "No se ha encontrado ningun contrato con ese identificador."

        resultado = [
            f"Estado del suministro para contrato {contrato['numero_contrato']}.",
            f"Titular: {contrato['nombre']} {contrato['apellidos']}.",
            f"Estado del contrato: {contrato['estado']}.",
        ]

        # 2. Active incidents affecting this supply address — either linked to the
        #    exact address, or covering a zone (street / postal code / municipality)
        #    that contains this address.
        incidencias = await conn.fetch(
            """
            SELECT DISTINCT i.id, i.tipo, i.descripcion, i.fecha_inicio, i.hora_inicio,
                   i.fecha_fin_prevista, i.hora_fin_prevista
            FROM incidencias i
            LEFT JOIN incidencia_direcciones idr ON i.id = idr.incidencia_id
            LEFT JOIN incidencia_zonas iz ON i.id = iz.incidencia_id
            WHERE i.fecha_fin IS NULL
              AND (
                  idr.direccion_suministro_id = $1
                  OR (iz.ambito = 'Calle'
                      AND LOWER(TRIM($2)) = LOWER(TRIM(iz.valor))
                      AND (iz.municipio IS NULL OR LOWER(iz.municipio) = LOWER($4)))
                  OR (iz.ambito = 'Codigo_postal' AND iz.valor = $3)
                  OR (iz.ambito = 'Municipio' AND LOWER(iz.valor) = LOWER($4))
              )
            ORDER BY i.fecha_inicio DESC
            """,
            contrato["dir_id"], contrato["calle"], contrato["cod_postal"], contrato["municipio"],
        )

        if incidencias:
            resultado.append(f"ATENCION: Hay {len(incidencias)} incidencia{'s' if len(incidencias) > 1 else ''} activa{'s' if len(incidencias) > 1 else ''} que afectan a esta direccion.")
            for inc in incidencias:
                fin_prev = ""
                if inc["fecha_fin_prevista"]:
                    fin_prev = f" Resolucion estimada: {inc['fecha_fin_prevista']}"
                    if inc["hora_fin_prevista"]:
                        fin_prev += f" a las {inc['hora_fin_prevista']}"
                    fin_prev += "."
                resultado.append(
                    f"Incidencia ID {inc['id']}: {inc['tipo']}, desde {inc['fecha_inicio']} "
                    f"a las {inc['hora_inicio']}. {inc['descripcion']}.{fin_prev}"
                )
        else:
            resultado.append("No hay incidencias activas que afecten a esta direccion.")

        # 3. Active cut expedients
        expedientes = await conn.fetch(
            """
            SELECT id, estado, fecha_apertura, fecha_corte, importe_deuda
            FROM expedientes_corte
            WHERE contrato_id = $1 AND estado NOT IN ('Cerrado')
            ORDER BY fecha_apertura DESC
            """,
            contrato_id,
        )

        if expedientes:
            resultado.append(f"ATENCION: Hay {len(expedientes)} expediente{'s' if len(expedientes) > 1 else ''} de corte activo{'s' if len(expedientes) > 1 else ''}.")
            for exp in expedientes:
                deuda = formatear_precio(float(exp["importe_deuda"])) if exp["importe_deuda"] else "sin importe registrado"
                corte = f", fecha de corte prevista: {exp['fecha_corte']}" if exp["fecha_corte"] else ""
                resultado.append(
                    f"Expediente ID {exp['id']}: estado {exp['estado']}, "
                    f"abierto el {exp['fecha_apertura']}{corte}. Deuda: {deuda}."
                )
        else:
            resultado.append("No hay expedientes de corte activos.")

        # 4. Last meter reading
        lectura = await conn.fetchrow(
            """
            SELECT num_serie, lectura_m3, fecha_lectura
            FROM contadores
            WHERE contrato_id = $1
            ORDER BY fecha_lectura DESC
            LIMIT 1
            """,
            contrato_id,
        )

        if lectura:
            resultado.append(
                f"Ultima lectura del contador {lectura['num_serie']}: "
                f"{lectura['lectura_m3']} metros cubicos, fecha {lectura['fecha_lectura']}."
            )
        else:
            resultado.append("No hay lecturas de contador registradas.")

        return " ".join(resultado)
    except Exception:
        return "Error al verificar el estado del suministro. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def obtener_contratos_abonado(entidad_id: int) -> str:
    """Lista todos los contratos de un abonado con su estado, direccion de suministro y fecha de alta."""
    conn = await obtener_conexion_db()
    try:
        contratos = await conn.fetch(
            """
            SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta, c.fecha_baja,
                   d.calle, d.numero, d.portal, d.planta, d.letra, d.cod_postal, d.municipio
            FROM contratos c
            JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
            WHERE c.entidad_id = $1
            ORDER BY c.fecha_alta
            """,
            entidad_id,
        )

        if not contratos:
            return "No se han encontrado contratos para este abonado."

        partes = []
        for c in contratos:
            dir_partes = [c["calle"]]
            if c["numero"]:
                dir_partes.append(c["numero"])
            if c["portal"]:
                dir_partes.append(f"portal {c['portal']}")
            if c["planta"]:
                dir_partes.append(f"planta {c['planta']}")
            if c["letra"]:
                dir_partes.append(c["letra"])
            dir_str = ", ".join(dir_partes) + f", {c['cod_postal']} {c['municipio']}"

            baja = f", baja {c['fecha_baja']}" if c["fecha_baja"] else ""
            partes.append(
                f"Contrato {c['numero_contrato']} (ID: {c['id']}): "
                f"estado {c['estado']}, alta {c['fecha_alta']}{baja}. "
                f"Direccion: {dir_str}"
            )

        return f"El abonado tiene {len(contratos)} contrato{'s' if len(contratos) > 1 else ''}. " + ". ".join(partes) + "."
    except Exception:
        return "Error al obtener los contratos. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
