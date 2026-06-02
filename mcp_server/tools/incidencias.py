from instance import mcp
from db import obtener_conexion_db
from validators import validar_tipo_incidencia


@mcp.tool()
async def consultar_incidencias_activas(zona: str = "", direccion: str = "") -> str:
    """Consulta incidencias activas (no resueltas ni cerradas). Puede filtrar por zona
    (municipio, ej: 'Villanueva') o por texto en la direccion afectada.
    Sin filtros, devuelve todas las incidencias abiertas o en progreso."""
    conn = await obtener_conexion_db()
    try:
        if direccion.strip():
            termino = f"%{direccion.strip()}%"
            filas = await conn.fetch(
                """
                SELECT DISTINCT i.id, i.tipo, i.descripcion, i.fecha_inicio, i.hora_inicio,
                       i.fecha_fin_prevista, i.hora_fin_prevista
                FROM incidencias i
                JOIN incidencia_direcciones id ON i.id = id.incidencia_id
                JOIN direcciones_suministro d ON id.direccion_suministro_id = d.id
                WHERE i.fecha_fin IS NULL
                  AND (LOWER(d.calle) LIKE LOWER($1) OR LOWER(d.municipio) LIKE LOWER($1))
                ORDER BY i.fecha_inicio DESC
                """,
                termino,
            )
        elif zona.strip():
            termino = f"%{zona.strip()}%"
            filas = await conn.fetch(
                """
                SELECT DISTINCT i.id, i.tipo, i.descripcion, i.fecha_inicio, i.hora_inicio,
                       i.fecha_fin_prevista, i.hora_fin_prevista
                FROM incidencias i
                JOIN incidencia_direcciones id ON i.id = id.incidencia_id
                JOIN direcciones_suministro d ON id.direccion_suministro_id = d.id
                WHERE i.fecha_fin IS NULL
                  AND LOWER(d.municipio) LIKE LOWER($1)
                ORDER BY i.fecha_inicio DESC
                """,
                termino,
            )
        else:
            filas = await conn.fetch(
                """
                SELECT id, tipo, descripcion, fecha_inicio, hora_inicio,
                       fecha_fin_prevista, hora_fin_prevista
                FROM incidencias
                WHERE fecha_fin IS NULL
                ORDER BY fecha_inicio DESC
                """,
            )

        if not filas:
            filtro = ""
            if direccion.strip():
                filtro = f" en la direccion '{direccion.strip()}'"
            elif zona.strip():
                filtro = f" en la zona '{zona.strip()}'"
            return f"No hay incidencias activas{filtro}."

        partes = []
        for i in filas:
            fin_prev = ""
            if i["fecha_fin_prevista"]:
                fin_prev = f" Resolucion estimada: {i['fecha_fin_prevista']}"
                if i["hora_fin_prevista"]:
                    fin_prev += f" a las {i['hora_fin_prevista']}"
                fin_prev += "."
            partes.append(
                f"Incidencia ID {i['id']}: tipo {i['tipo']}, desde {i['fecha_inicio']} "
                f"a las {i['hora_inicio']}. {i['descripcion']}.{fin_prev}"
            )

        return f"Se han encontrado {len(filas)} incidencia{'s' if len(filas) > 1 else ''} activa{'s' if len(filas) > 1 else ''}. " + " ".join(partes)
    except Exception:
        return "Error al consultar las incidencias. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def obtener_detalle_incidencia(incidencia_id: int) -> str:
    """Devuelve el detalle completo de una incidencia: tipo, estado, descripcion,
    fechas y direcciones afectadas."""
    conn = await obtener_conexion_db()
    try:
        inc = await conn.fetchrow(
            """
            SELECT id, tipo, fecha_inicio, hora_inicio, fecha_fin, hora_fin,
                   fecha_fin_prevista, hora_fin_prevista, descripcion
            FROM incidencias WHERE id = $1
            """,
            incidencia_id,
        )
        if not inc:
            return "No se ha encontrado ninguna incidencia con ese identificador."

        estado = "Resuelta" if inc["fecha_fin"] else "Activa"

        resultado = [
            f"Incidencia ID {inc['id']}. Tipo: {inc['tipo']}. Estado: {estado}.",
            f"Descripcion: {inc['descripcion']}.",
            f"Inicio: {inc['fecha_inicio']} a las {inc['hora_inicio']}.",
        ]

        if inc["fecha_fin"]:
            resultado.append(f"Fin: {inc['fecha_fin']} a las {inc['hora_fin']}.")
        elif inc["fecha_fin_prevista"]:
            hora = f" a las {inc['hora_fin_prevista']}" if inc["hora_fin_prevista"] else ""
            resultado.append(f"Resolucion estimada: {inc['fecha_fin_prevista']}{hora}.")

        # Affected addresses
        direcciones = await conn.fetch(
            """
            SELECT d.calle, d.numero, d.portal, d.planta, d.letra, d.cod_postal, d.municipio
            FROM incidencia_direcciones id
            JOIN direcciones_suministro d ON id.direccion_suministro_id = d.id
            WHERE id.incidencia_id = $1
            """,
            incidencia_id,
        )

        if direcciones:
            dirs = []
            for d in direcciones:
                partes = [d["calle"]]
                if d["numero"]:
                    partes.append(d["numero"])
                if d["portal"]:
                    partes.append(f"portal {d['portal']}")
                if d["planta"]:
                    partes.append(f"planta {d['planta']}")
                if d["letra"]:
                    partes.append(d["letra"])
                dirs.append(", ".join(partes) + f", {d['cod_postal']} {d['municipio']}")
            resultado.append(f"Direcciones afectadas: " + "; ".join(dirs) + ".")
        else:
            resultado.append("No tiene direcciones afectadas registradas.")

        return " ".join(resultado)
    except Exception:
        return "Error al obtener el detalle de la incidencia. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def crear_incidencia(
    tipo: str,
    descripcion: str,
    direccion_suministro_ids: str = "",
) -> str:
    """Crea una nueva incidencia en el sistema.
    tipo: Averia, Corte_programado, Corte_impago, Fuga.
    direccion_suministro_ids: IDs de direcciones afectadas separados por coma (opcional)."""
    error = validar_tipo_incidencia(tipo)
    if error:
        return error

    if not descripcion.strip():
        return "La descripcion de la incidencia es obligatoria."

    # Parse address IDs if provided
    dir_ids = []
    if direccion_suministro_ids.strip():
        try:
            dir_ids = [int(x.strip()) for x in direccion_suministro_ids.split(",") if x.strip()]
        except ValueError:
            return "direccion_suministro_ids debe ser una lista de IDs separados por coma."

    conn = await obtener_conexion_db()
    try:
        from datetime import date, datetime

        hoy = date.today()
        ahora = datetime.now().time()

        async with conn.transaction():
            inc_id = await conn.fetchval(
                """
                INSERT INTO incidencias (tipo, fecha_inicio, hora_inicio, descripcion)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                tipo, hoy, ahora, descripcion.strip(),
            )

            for did in dir_ids:
                # Verify address exists
                exists = await conn.fetchval(
                    "SELECT id FROM direcciones_suministro WHERE id = $1", did
                )
                if not exists:
                    return f"No se ha encontrado la direccion de suministro con ID {did}."
                await conn.execute(
                    "INSERT INTO incidencia_direcciones (incidencia_id, direccion_suministro_id) VALUES ($1, $2)",
                    inc_id, did,
                )

        dirs_msg = ""
        if dir_ids:
            dirs_msg = f" Se han vinculado {len(dir_ids)} direccion{'es' if len(dir_ids) > 1 else ''} afectada{'s' if len(dir_ids) > 1 else ''}."

        return (
            f"Incidencia creada correctamente con ID {inc_id}. "
            f"Tipo: {tipo}. {descripcion.strip()}.{dirs_msg}"
        )
    except Exception:
        return "Error al crear la incidencia. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
