from instance import mcp
from db import obtener_conexion_db
from validators import generar_numero_parte


@mcp.tool()
async def crear_parte_trabajo(
    descripcion: str,
    direccion_suministro_id: int = 0,
    incidencia_id: int = 0,
) -> str:
    """Crea un nuevo parte de trabajo (ticket). Genera automaticamente un numero de parte.
    Al menos uno de direccion_suministro_id o incidencia_id debe ser proporcionado."""
    if not descripcion.strip():
        return "La descripcion del parte de trabajo es obligatoria."

    if direccion_suministro_id == 0 and incidencia_id == 0:
        return "Debe indicar al menos una direccion de suministro o una incidencia asociada."

    conn = await obtener_conexion_db()
    try:
        # Validate references
        if direccion_suministro_id:
            exists = await conn.fetchval(
                "SELECT id FROM direcciones_suministro WHERE id = $1",
                direccion_suministro_id,
            )
            if not exists:
                return f"No se ha encontrado la direccion de suministro con ID {direccion_suministro_id}."

        if incidencia_id:
            exists = await conn.fetchval(
                "SELECT id FROM incidencias WHERE id = $1",
                incidencia_id,
            )
            if not exists:
                return f"No se ha encontrado la incidencia con ID {incidencia_id}."

        # Generate part number
        ultimo = await conn.fetchval("SELECT COALESCE(MAX(id), 0) FROM partes_trabajo")
        numero_parte = generar_numero_parte(ultimo + 1)

        parte_id = await conn.fetchval(
            """
            INSERT INTO partes_trabajo (numero_parte, direccion_suministro_id, incidencia_id, descripcion)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            numero_parte,
            direccion_suministro_id if direccion_suministro_id else None,
            incidencia_id if incidencia_id else None,
            descripcion.strip(),
        )

        return (
            f"Parte de trabajo creado correctamente. Numero de parte: {numero_parte} (ID: {parte_id}). "
            f"Estado: Abierto. {descripcion.strip()}."
        )
    except Exception:
        return "Error al crear el parte de trabajo. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def consultar_partes_trabajo(
    incidencia_id: int = 0,
    direccion_id: int = 0,
) -> str:
    """Consulta partes de trabajo existentes. Puede filtrar por incidencia o direccion de suministro.
    Sin filtros, devuelve los partes abiertos o en proceso."""
    conn = await obtener_conexion_db()
    try:
        if incidencia_id:
            filas = await conn.fetch(
                """
                SELECT pt.id, pt.numero_parte, pt.estado, pt.fecha, pt.descripcion,
                       d.calle, d.numero, d.municipio
                FROM partes_trabajo pt
                LEFT JOIN direcciones_suministro d ON pt.direccion_suministro_id = d.id
                WHERE pt.incidencia_id = $1
                ORDER BY pt.fecha DESC
                """,
                incidencia_id,
            )
        elif direccion_id:
            filas = await conn.fetch(
                """
                SELECT pt.id, pt.numero_parte, pt.estado, pt.fecha, pt.descripcion,
                       d.calle, d.numero, d.municipio
                FROM partes_trabajo pt
                LEFT JOIN direcciones_suministro d ON pt.direccion_suministro_id = d.id
                WHERE pt.direccion_suministro_id = $1
                ORDER BY pt.fecha DESC
                """,
                direccion_id,
            )
        else:
            filas = await conn.fetch(
                """
                SELECT pt.id, pt.numero_parte, pt.estado, pt.fecha, pt.descripcion,
                       d.calle, d.numero, d.municipio
                FROM partes_trabajo pt
                LEFT JOIN direcciones_suministro d ON pt.direccion_suministro_id = d.id
                WHERE pt.estado IN ('Abierto', 'En_proceso')
                ORDER BY pt.fecha DESC
                """,
            )

        if not filas:
            return "No se han encontrado partes de trabajo con esos criterios."

        partes = []
        for pt in filas:
            dir_str = ""
            if pt["calle"]:
                dir_str = f", direccion: {pt['calle']}"
                if pt["numero"]:
                    dir_str += f" {pt['numero']}"
                if pt["municipio"]:
                    dir_str += f", {pt['municipio']}"
            partes.append(
                f"Parte {pt['numero_parte']} (ID: {pt['id']}): estado {pt['estado']}, "
                f"fecha {pt['fecha']}{dir_str}. {pt['descripcion']}"
            )

        return f"{len(filas)} parte{'s' if len(filas) > 1 else ''} de trabajo encontrado{'s' if len(filas) > 1 else ''}. " + ". ".join(partes) + "."
    except Exception:
        return "Error al consultar los partes de trabajo. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
