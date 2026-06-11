"""Reference data for the frontend: ENUM values for dropdowns."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/meta", tags=["meta"])

ENUMS = {
    "estado_contrato": ["Activo", "Suspendido", "Baja"],
    "estado_recibo": ["Pendiente", "Pagado", "Impagado", "Devuelto"],
    "forma_pago": ["Efectivo", "Transferencia", "Domiciliado"],
    "estado_expediente": ["Pendiente", "Notificado", "Ejecutado", "Cerrado"],
    "tipo_incidencia": ["Averia", "Corte_programado", "Corte_impago", "Fuga"],
    "estado_parte": ["Abierto", "En_proceso", "Cerrado"],
    "motivo_llamada": [
        "Sin_suministro", "Fuga", "Consulta_factura", "Reclamacion", "Informacion", "Otro"
    ],
    "estado_llamada": ["Completada", "Escalada", "Abandonada"],
}


@router.get("/enums")
async def get_enums():
    return ENUMS
