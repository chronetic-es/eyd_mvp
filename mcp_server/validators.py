from datetime import date


def validar_nif(nif: str) -> str | None:
    """Valida formato basico de NIF/CIF. Devuelve mensaje de error o None."""
    nif = nif.strip().upper()
    if len(nif) < 8 or len(nif) > 12:
        return "El NIF no parece valido. Debe tener entre 8 y 12 caracteres."
    return None


def validar_telefono(telefono: str) -> str | None:
    """Valida que el telefono sea razonablemente valido."""
    digitos = "".join(c for c in telefono if c.isdigit())
    if len(digitos) < 7 or len(telefono) > 25:
        return "El numero de telefono no parece valido."
    return None


def normalizar_telefono(telefono: str) -> str:
    """Devuelve solo los digitos del numero nacional (ultimos 9), ignorando prefijos."""
    digitos = "".join(c for c in telefono if c.isdigit())
    # Quita prefijo internacional español si viene como 0034...
    if digitos.startswith("0034"):
        digitos = digitos[4:]
    # Nos quedamos con los ultimos 9 digitos (numero nacional ES)
    return digitos[-9:]

def formatear_precio(valor: float) -> str:
    """Convierte un precio decimal a texto legible por TTS."""
    centimos_total = round(valor * 100)
    euros = centimos_total // 100
    cts = centimos_total % 100
    if cts == 0:
        return f"{euros} euros"
    return f"{euros} euros con {cts} centimos"


def validar_tipo_incidencia(tipo: str) -> str | None:
    """Valida que el tipo de incidencia sea uno de los permitidos."""
    tipos_validos = {"Averia", "Corte_programado", "Corte_impago", "Fuga"}
    if tipo not in tipos_validos:
        return f"Tipo de incidencia no valido. Valores permitidos: {', '.join(sorted(tipos_validos))}."
    return None


def validar_motivo_llamada(motivo: str) -> str | None:
    """Valida que el motivo de llamada sea uno de los permitidos."""
    motivos_validos = {
        "Sin_suministro", "Fuga", "Consulta_factura",
        "Reclamacion", "Informacion", "Otro",
    }
    if motivo not in motivos_validos:
        return f"Motivo de llamada no valido. Valores permitidos: {', '.join(sorted(motivos_validos))}."
    return None


def validar_estado_llamada(estado: str) -> str | None:
    """Valida que el estado de la llamada sea uno de los permitidos."""
    estados_validos = {"Completada", "Escalada", "Abandonada"}
    if estado not in estados_validos:
        return f"Estado de llamada no valido. Valores permitidos: {', '.join(sorted(estados_validos))}."
    return None


def generar_numero_parte(ultimo_id: int) -> str:
    """Genera el siguiente numero de parte con formato PT-YYYY-NNNN."""
    year = date.today().year
    return f"PT-{year}-{ultimo_id:04d}"
