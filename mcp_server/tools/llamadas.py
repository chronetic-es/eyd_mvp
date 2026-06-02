from instance import mcp
from db import obtener_conexion_db
from validators import validar_telefono, validar_motivo_llamada, validar_estado_llamada


@mcp.tool()
async def registrar_llamada(
    telefono: str,
    motivo: str,
    resumen: str,
    estado: str = "Completada",
    human_handoff: bool = False,
) -> str:
    """Registra una llamada atendida en el sistema. Debe llamarse al finalizar cada llamada.
    motivo: Sin_suministro, Fuga, Consulta_factura, Reclamacion, Informacion, Otro.
    estado: Completada, Escalada, Abandonada."""
    error = validar_telefono(telefono)
    if error:
        return error

    error = validar_motivo_llamada(motivo)
    if error:
        return error

    error = validar_estado_llamada(estado)
    if error:
        return error

    if not resumen.strip():
        return "El resumen de la llamada es obligatorio."

    conn = await obtener_conexion_db()
    try:
        llamada_id = await conn.fetchval(
            """
            INSERT INTO llamadas (telefono, motivo_detectado, resumen_ia, estado, human_handoff)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            telefono.strip(), motivo, resumen.strip(), estado, human_handoff,
        )

        return f"Llamada registrada correctamente con ID {llamada_id}."
    except Exception:
        return "Error al registrar la llamada. Por favor, intentelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def finalizar_llamada() -> str:
    """Finaliza la llamada actual. Debe usarse solo tras despedirse del abonado
    y haber registrado la llamada con registrar_llamada."""
    return "Llamada finalizada correctamente."
