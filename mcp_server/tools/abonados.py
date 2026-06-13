from datetime import date, timedelta

from instance import mcp
from db import obtener_conexion_db
from validators import validar_nif, validar_telefono, normalizar_telefono

_DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _formatear_direccion(row) -> str:
    """Construye una direccion legible a partir de los campos de direcciones_suministro."""
    partes = [row["calle"]]
    if row["numero"]:
        partes.append(row["numero"])
    if row["portal"]:
        partes.append(f"portal {row['portal']}")
    if row["planta"]:
        partes.append(f"planta {row['planta']}")
    if row["letra"]:
        partes.append(row["letra"])
    return ", ".join(partes) + f", {row['cod_postal']} {row['municipio']}"


@mcp.tool()
async def obtener_fecha_actual() -> str:
    """Devuelve la fecha actual con el dia de la semana en espanol, para calcular fechas relativas."""
    hoy = date.today()
    dia_semana = _DIAS_ES[hoy.weekday()]
    mes = _MESES_ES[hoy.month - 1]
    return (
        f"Hoy es {dia_semana}, {hoy.day} de {mes} de {hoy.year}. "
        f"Fecha ISO: {hoy.isoformat()}."
    )


@mcp.tool()
async def buscar_abonado_por_nif(nif: str) -> str:
    """Busca un abonado por su NIF/CIF. Devuelve sus datos personales y contratos asociados."""
    error = validar_nif(nif)
    if error:
        return error

    conn = await obtener_conexion_db()
    try:
        entidad = await conn.fetchrow(
            "SELECT id, nif, nombre, apellidos, telefono, dir_fiscal "
            "FROM entidades WHERE UPPER(nif) = UPPER($1)",
            nif.strip(),
        )
        if not entidad:
            return "No se ha encontrado ningun abonado con ese NIF."

        contratos = await conn.fetch(
            """
            SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta,
                   d.calle, d.numero, d.portal, d.planta, d.letra, d.cod_postal, d.municipio
            FROM contratos c
            JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
            WHERE c.entidad_id = $1
            ORDER BY c.fecha_alta
            """,
            entidad["id"],
        )

        info = (
            f"Abonado encontrado. ID: {entidad['id']}. "
            f"Nombre: {entidad['nombre']} {entidad['apellidos']}. "
            f"NIF: {entidad['nif']}. Telefono: {entidad['telefono']}. "
            f"Direccion fiscal: {entidad['dir_fiscal']}."
        )

        if contratos:
            partes = []
            for c in contratos:
                dir_str = _formatear_direccion(c)
                partes.append(
                    f"Contrato {c['numero_contrato']} (ID: {c['id']}), "
                    f"estado {c['estado']}, alta {c['fecha_alta']}, "
                    f"direccion de suministro: {dir_str}"
                )
            info += f" Tiene {len(contratos)} contrato{'s' if len(contratos) > 1 else ''}. " + ". ".join(partes) + "."
        else:
            info += " No tiene contratos asociados."

        return info
    except Exception:
        return "Error al buscar el abonado. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def buscar_abonado_por_telefono(telefono: str) -> str:
    """Busca un abonado por su numero de telefono. Devuelve sus datos personales y contratos asociados."""
    error = validar_telefono(telefono)
    if error:
        return error
    conn = await obtener_conexion_db()
    try:
        tel_norm = normalizar_telefono(telefono)
        entidad = await conn.fetchrow(
            "SELECT id, nif, nombre, apellidos, telefono, dir_fiscal "
            "FROM entidades "
            "WHERE right(regexp_replace(telefono, '\\D', '', 'g'), 9) = $1",
            tel_norm,
        )
        if not entidad:
            return "No se ha encontrado ningun abonado con ese numero de telefono."
        contratos = await conn.fetch(
            """
            SELECT c.id, c.numero_contrato, c.estado, c.fecha_alta,
                   d.calle, d.numero, d.portal, d.planta, d.letra, d.cod_postal, d.municipio
            FROM contratos c
            JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
            WHERE c.entidad_id = $1
            ORDER BY c.fecha_alta
            """,
            entidad["id"],
        )
        info = (
            f"Abonado encontrado. ID: {entidad['id']}. "
            f"Nombre: {entidad['nombre']} {entidad['apellidos']}. "
            f"NIF: {entidad['nif']}. Telefono: {entidad['telefono']}. "
            f"Direccion fiscal: {entidad['dir_fiscal']}."
        )
        if contratos:
            partes = []
            for c in contratos:
                dir_str = _formatear_direccion(c)
                partes.append(
                    f"Contrato {c['numero_contrato']} (ID: {c['id']}), "
                    f"estado {c['estado']}, alta {c['fecha_alta']}, "
                    f"direccion de suministro: {dir_str}"
                )
            info += f" Tiene {len(contratos)} contrato{'s' if len(contratos) > 1 else ''}. " + ". ".join(partes) + "."
        else:
            info += " No tiene contratos asociados."
        return info
    except Exception:
        return "Error al buscar el abonado. Por favor, intentelo de nuevo."
    finally:
        await conn.close()

@mcp.tool()
async def buscar_abonado_por_direccion(direccion: str) -> str:
    """Busca abonados cuya direccion de suministro coincida parcialmente con el texto indicado.
    Devuelve los abonados encontrados con sus contratos."""
    if not direccion or len(direccion.strip()) < 3:
        return "Debe indicar al menos 3 caracteres de la direccion para buscar."

    conn = await obtener_conexion_db()
    try:
        termino = f"%{direccion.strip()}%"
        filas = await conn.fetch(
            """
            SELECT DISTINCT e.id, e.nif, e.nombre, e.apellidos, e.telefono,
                   c.id AS contrato_id, c.numero_contrato, c.estado,
                   d.calle, d.numero, d.portal, d.planta, d.letra, d.cod_postal, d.municipio
            FROM entidades e
            JOIN contratos c ON c.entidad_id = e.id
            JOIN direcciones_suministro d ON c.direccion_suministro_id = d.id
            WHERE LOWER(d.calle) LIKE LOWER($1)
               OR LOWER(d.municipio) LIKE LOWER($1)
               OR LOWER(CONCAT(d.calle, ' ', d.numero)) LIKE LOWER($1)
            ORDER BY e.apellidos, e.nombre
            """,
            termino,
        )

        if not filas:
            return "No se han encontrado abonados con esa direccion de suministro."

        # Group by entity
        entidades = {}
        for f in filas:
            eid = f["id"]
            if eid not in entidades:
                entidades[eid] = {
                    "info": f"Abonado ID: {eid}, {f['nombre']} {f['apellidos']}, NIF: {f['nif']}, telefono: {f['telefono']}",
                    "contratos": [],
                }
            dir_str = _formatear_direccion(f)
            entidades[eid]["contratos"].append(
                f"Contrato {f['numero_contrato']} (ID: {f['contrato_id']}), estado {f['estado']}, direccion: {dir_str}"
            )

        partes = []
        for e in entidades.values():
            contratos_str = ". ".join(e["contratos"])
            partes.append(f"{e['info']}. {contratos_str}.")

        return f"Se han encontrado {len(entidades)} abonado{'s' if len(entidades) > 1 else ''}. " + " ".join(partes)
    except Exception:
        return "Error al buscar por direccion. Por favor, intentelo de nuevo."
    finally:
        await conn.close()
