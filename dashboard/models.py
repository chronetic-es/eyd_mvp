"""Pydantic request models for create/update operations.

ENUM values mirror database/init-db.sql. Optional fields on the *Update models
allow partial edits; routers apply only the provided fields.
"""
import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ─── ENUM literals (mirror init-db.sql) ──────────────────
EstadoContrato = Literal["Activo", "Suspendido", "Baja"]
EstadoRecibo = Literal["Pendiente", "Pagado", "Impagado", "Devuelto"]
FormaPago = Literal["Efectivo", "Transferencia", "Domiciliado"]
EstadoExpediente = Literal["Pendiente", "Notificado", "Ejecutado", "Cerrado"]
TipoIncidencia = Literal["Averia", "Corte_programado", "Corte_impago", "Fuga"]
EstadoParte = Literal["Abierto", "En_proceso", "Cerrado"]
MotivoLlamada = Literal[
    "Sin_suministro", "Fuga", "Consulta_factura", "Reclamacion", "Informacion", "Otro"
]
EstadoLlamada = Literal["Completada", "Escalada", "Abandonada"]


# ─── ABONADOS (entidades) ────────────────────────────────
class AbonadoIn(BaseModel):
    nif: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=150)
    telefono: str = Field(min_length=1, max_length=20)
    dir_fiscal: str = Field(min_length=1, max_length=250)


class AbonadoUpdate(BaseModel):
    nif: Optional[str] = Field(default=None, max_length=20)
    nombre: Optional[str] = Field(default=None, max_length=100)
    apellidos: Optional[str] = Field(default=None, max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=20)
    dir_fiscal: Optional[str] = Field(default=None, max_length=250)


# ─── DIRECCIONES ─────────────────────────────────────────
class DireccionIn(BaseModel):
    calle: str = Field(min_length=1, max_length=200)
    numero: Optional[str] = Field(default=None, max_length=10)
    portal: Optional[str] = Field(default=None, max_length=10)
    planta: Optional[str] = Field(default=None, max_length=10)
    letra: Optional[str] = Field(default=None, max_length=10)
    cod_postal: str = Field(min_length=1, max_length=10)
    municipio: str = Field(min_length=1, max_length=100)


class DireccionUpdate(BaseModel):
    calle: Optional[str] = Field(default=None, max_length=200)
    numero: Optional[str] = Field(default=None, max_length=10)
    portal: Optional[str] = Field(default=None, max_length=10)
    planta: Optional[str] = Field(default=None, max_length=10)
    letra: Optional[str] = Field(default=None, max_length=10)
    cod_postal: Optional[str] = Field(default=None, max_length=10)
    municipio: Optional[str] = Field(default=None, max_length=100)


# ─── CONTRATOS ───────────────────────────────────────────
class ContratoIn(BaseModel):
    numero_contrato: str = Field(min_length=1, max_length=20)
    entidad_id: int
    direccion_suministro_id: int
    estado: EstadoContrato = "Activo"
    fecha_alta: datetime.date
    fecha_baja: Optional[datetime.date] = None


class ContratoUpdate(BaseModel):
    numero_contrato: Optional[str] = Field(default=None, max_length=20)
    entidad_id: Optional[int] = None
    direccion_suministro_id: Optional[int] = None
    estado: Optional[EstadoContrato] = None
    fecha_alta: Optional[datetime.date] = None
    fecha_baja: Optional[datetime.date] = None


# ─── CONTADORES ──────────────────────────────────────────
class ContadorIn(BaseModel):
    contrato_id: int
    num_serie: str = Field(min_length=1, max_length=30)
    fecha_alta: datetime.date
    fecha_baja: Optional[datetime.date] = None
    lectura_m3: Decimal = Decimal("0")
    fecha_lectura: datetime.date


class ContadorUpdate(BaseModel):
    num_serie: Optional[str] = Field(default=None, max_length=30)
    fecha_alta: Optional[datetime.date] = None
    fecha_baja: Optional[datetime.date] = None
    lectura_m3: Optional[Decimal] = None
    fecha_lectura: Optional[datetime.date] = None


# ─── RECIBOS ─────────────────────────────────────────────
class ReciboIn(BaseModel):
    contrato_id: int
    periodo: str = Field(min_length=1, max_length=20)
    importe: Decimal = Field(ge=0)
    estado: EstadoRecibo = "Pendiente"
    forma_pago: FormaPago = "Domiciliado"
    fecha_emision: datetime.date
    fecha_vencimiento: datetime.date


class ReciboUpdate(BaseModel):
    contrato_id: Optional[int] = None
    periodo: Optional[str] = Field(default=None, max_length=20)
    importe: Optional[Decimal] = Field(default=None, ge=0)
    estado: Optional[EstadoRecibo] = None
    forma_pago: Optional[FormaPago] = None
    fecha_emision: Optional[datetime.date] = None
    fecha_vencimiento: Optional[datetime.date] = None


# ─── EXPEDIENTES ─────────────────────────────────────────
class ExpedienteIn(BaseModel):
    contrato_id: int
    recibo_id: Optional[int] = None
    fecha_apertura: datetime.date
    fecha_corte: Optional[datetime.date] = None
    estado: EstadoExpediente = "Pendiente"
    importe_deuda: Optional[Decimal] = Field(default=None, ge=0)


class ExpedienteUpdate(BaseModel):
    contrato_id: Optional[int] = None
    recibo_id: Optional[int] = None
    fecha_apertura: Optional[datetime.date] = None
    fecha_corte: Optional[datetime.date] = None
    estado: Optional[EstadoExpediente] = None
    importe_deuda: Optional[Decimal] = Field(default=None, ge=0)


# ─── INCIDENCIAS ─────────────────────────────────────────
class IncidenciaIn(BaseModel):
    tipo: TipoIncidencia
    fecha_inicio: datetime.date
    hora_inicio: datetime.time
    fecha_fin: Optional[datetime.date] = None
    hora_fin: Optional[datetime.time] = None
    fecha_fin_prevista: Optional[datetime.date] = None
    hora_fin_prevista: Optional[datetime.time] = None
    descripcion: str = Field(min_length=1)


class IncidenciaUpdate(BaseModel):
    tipo: Optional[TipoIncidencia] = None
    fecha_inicio: Optional[datetime.date] = None
    hora_inicio: Optional[datetime.time] = None
    fecha_fin: Optional[datetime.date] = None
    hora_fin: Optional[datetime.time] = None
    fecha_fin_prevista: Optional[datetime.date] = None
    hora_fin_prevista: Optional[datetime.time] = None
    descripcion: Optional[str] = None


class DireccionLink(BaseModel):
    direccion_suministro_id: int


AmbitoIncidencia = Literal["Calle", "Codigo_postal", "Municipio"]


class ZonaLink(BaseModel):
    ambito: AmbitoIncidencia
    valor: str = Field(min_length=1, max_length=200)
    municipio: Optional[str] = Field(default=None, max_length=100)


# ─── PARTES DE TRABAJO ───────────────────────────────────
class ParteIn(BaseModel):
    direccion_suministro_id: Optional[int] = None
    incidencia_id: Optional[int] = None
    fecha: Optional[datetime.date] = None
    estado: EstadoParte = "Abierto"
    descripcion: str = Field(min_length=1)


class ParteUpdate(BaseModel):
    direccion_suministro_id: Optional[int] = None
    incidencia_id: Optional[int] = None
    fecha: Optional[datetime.date] = None
    estado: Optional[EstadoParte] = None
    descripcion: Optional[str] = None


# ─── LLAMADAS ────────────────────────────────────────────
class LlamadaUpdate(BaseModel):
    telefono: Optional[str] = Field(default=None, max_length=20)
    resumen_ia: Optional[str] = None
    transcripcion: Optional[str] = None
    motivo_detectado: Optional[MotivoLlamada] = None
    human_handoff: Optional[bool] = None
    estado: Optional[EstadoLlamada] = None
