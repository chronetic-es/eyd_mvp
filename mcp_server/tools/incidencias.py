from instance import mcp
from db import obtener_conexion_db
from validators import validar_tipo_incidencia, generar_numero_parte


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
                LEFT JOIN incidencia_direcciones idl ON i.id = idl.incidencia_id
                LEFT JOIN direcciones_suministro d ON idl.direccion_suministro_id = d.id
                LEFT JOIN incidencia_zonas iz ON i.id = iz.incidencia_id
                WHERE i.fecha_fin IS NULL
                  AND (LOWER(d.calle) LIKE LOWER($1) OR LOWER(d.municipio) LIKE LOWER($1)
                       OR LOWER(iz.valor) LIKE LOWER($1) OR LOWER(iz.municipio) LIKE LOWER($1))
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
                LEFT JOIN incidencia_direcciones idl ON i.id = idl.incidencia_id
                LEFT JOIN direcciones_suministro d ON idl.direccion_suministro_id = d.id
                LEFT JOIN incidencia_zonas iz ON i.id = iz.incidencia_id
                WHERE i.fecha_fin IS NULL
                  AND (LOWER(d.municipio) LIKE LOWER($1)
                       OR (iz.ambito = 'Municipio' AND LOWER(iz.valor) LIKE LOWER($1))
                       OR (iz.ambito = 'Calle' AND LOWER(iz.municipio) LIKE LOWER($1)))
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
            resultado.append(f"Direcciones concretas afectadas: " + "; ".join(dirs) + ".")
        else:
            resultado.append("No tiene direcciones concretas afectadas registradas.")

        # Affected zones (general scope)
        zonas = await conn.fetch(
            "SELECT ambito, valor, municipio FROM incidencia_zonas WHERE incidencia_id = $1",
            incidencia_id,
        )
        if zonas:
            descs = []
            for z in zonas:
                if z["ambito"] == "Calle":
                    descs.append(f"calle {z['valor']}" + (f" ({z['municipio']})" if z["municipio"] else ""))
                elif z["ambito"] == "Codigo_postal":
                    descs.append(f"codigo postal {z['valor']}")
                else:
                    descs.append(f"municipio {z['valor']}")
            resultado.append("Ambito general afectado: " + "; ".join(descs) + ".")

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
    zona_calle: str = "",
    zona_cod_postal: str = "",
    zona_municipio: str = "",
    contrato_id: int = 0,
    generar_parte: bool = True,
    descripcion_parte: str = "",
) -> str:
    """Crea una nueva incidencia y, salvo que se indique lo contrario, su parte de trabajo
    asociado, todo de forma atomica (o se crean ambos o ninguno).
    tipo: Averia, Corte_programado, Corte_impago, Fuga.
    direccion_suministro_ids: IDs de direcciones concretas afectadas separados por coma (opcional).
    contrato_id: para una incidencia que afecta solo al domicilio de un abonado concreto (ej: Flujo B,
      falta de agua sin causa conocida). La incidencia se acota a la direccion de suministro de ese
      contrato, sin afectar a vecinos.
    Para una incidencia de ambito general (afecta a todos los abonados de una zona), indica:
    zona_calle: nombre de la calle afectada (ej: 'Calle del Rio'); usa zona_municipio para acotarla.
    zona_cod_postal: codigo postal afectado (ej: '28002').
    zona_municipio: municipio afectado (ej: 'Villanueva'); si se indica sin zona_calle, afecta a todo el municipio.
    generar_parte: si es True (por defecto), crea tambien un parte de trabajo vinculado a la incidencia.
    descripcion_parte: descripcion del parte (si se omite, se usa la de la incidencia).
    Cualquier abonado cuya direccion de suministro caiga dentro de la zona quedara afectado."""
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

    # Build affected zones (ambito, valor, municipio)
    zonas = []
    if zona_calle.strip():
        zonas.append(("Calle", zona_calle.strip(), zona_municipio.strip() or None))
    if zona_cod_postal.strip():
        zonas.append(("Codigo_postal", zona_cod_postal.strip(), None))
    if zona_municipio.strip() and not zona_calle.strip():
        zonas.append(("Municipio", zona_municipio.strip(), None))

    conn = await obtener_conexion_db()
    try:
        from datetime import date, datetime

        # --- Validate ALL references BEFORE opening the transaction (atomicity) ---
        for did in dir_ids:
            exists = await conn.fetchval(
                "SELECT id FROM direcciones_suministro WHERE id = $1", did
            )
            if not exists:
                return f"No se ha encontrado la direccion de suministro con ID {did}."

        contrato_dir_id = None
        if contrato_id:
            contrato_dir_id = await conn.fetchval(
                "SELECT direccion_suministro_id FROM contratos WHERE id = $1", contrato_id
            )
            if not contrato_dir_id:
                return f"No se ha encontrado el contrato con ID {contrato_id}."

        # Address to link + use as the work order's location (contract address takes priority)
        direcciones_a_enlazar = list(dict.fromkeys(
            ([contrato_dir_id] if contrato_dir_id else []) + dir_ids
        ))
        direccion_parte = contrato_dir_id or (dir_ids[0] if dir_ids else None)

        hoy = date.today()
        ahora = datetime.now().time()
        numero_parte = None

        async with conn.transaction():
            inc_id = await conn.fetchval(
                """
                INSERT INTO incidencias (tipo, fecha_inicio, hora_inicio, descripcion)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                tipo, hoy, ahora, descripcion.strip(),
            )

            for did in direcciones_a_enlazar:
                await conn.execute(
                    "INSERT INTO incidencia_direcciones (incidencia_id, direccion_suministro_id) VALUES ($1, $2)",
                    inc_id, did,
                )

            for ambito, valor, municipio in zonas:
                await conn.execute(
                    "INSERT INTO incidencia_zonas (incidencia_id, ambito, valor, municipio) VALUES ($1, $2, $3, $4)",
                    inc_id, ambito, valor, municipio,
                )

            if generar_parte:
                ultimo = await conn.fetchval("SELECT COALESCE(MAX(id), 0) FROM partes_trabajo")
                numero_parte = generar_numero_parte(ultimo + 1)
                desc_pt = descripcion_parte.strip() or descripcion.strip()
                await conn.execute(
                    """
                    INSERT INTO partes_trabajo (numero_parte, direccion_suministro_id, incidencia_id, descripcion)
                    VALUES ($1, $2, $3, $4)
                    """,
                    numero_parte, direccion_parte, inc_id, desc_pt,
                )

        dirs_msg = ""
        if direcciones_a_enlazar:
            n = len(direcciones_a_enlazar)
            dirs_msg = f" Se ha{'n' if n > 1 else ''} vinculado {n} direccion{'es' if n > 1 else ''} concreta{'s' if n > 1 else ''}."
        zonas_msg = ""
        if zonas:
            desc_zonas = "; ".join(
                f"{a.lower()} {v}" + (f" ({m})" if m else "") for a, v, m in zonas
            )
            zonas_msg = f" Ambito general afectado: {desc_zonas}."
        parte_msg = f" Se ha generado el parte de trabajo {numero_parte}." if numero_parte else ""

        return (
            f"Incidencia creada correctamente con ID {inc_id}. "
            f"Tipo: {tipo}. {descripcion.strip()}.{dirs_msg}{zonas_msg}{parte_msg}"
        )
    except Exception:
        return "Error al crear la incidencia. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
