from pathlib import Path

from instance import mcp

_INFO_FILE = Path(__file__).parent.parent / "empresa_info.txt"


@mcp.tool()
def obtener_informacion_empresa() -> str:
    """Devuelve la informacion general de la empresa de suministro de agua:
    nombre, horarios, telefonos de emergencia, oficinas, tarifas, politicas."""
    return _INFO_FILE.read_text(encoding="utf-8")
