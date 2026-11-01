"""Value Objects: se comparan por su valor, no por identidad (Etapa 3)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from enum import Enum


@dataclass(frozen=True, order=True)
class Dinero:
    monto: Decimal
    moneda: str = "MXN"

    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El dinero no puede ser negativo")

    @staticmethod
    def mxn(valor) -> "Dinero":
        return Dinero(Decimal(str(valor)))

    @staticmethod
    def cero() -> "Dinero":
        return Dinero(Decimal("0"))

    def __add__(self, otro: "Dinero") -> "Dinero":
        return Dinero(self.monto + otro.monto, self.moneda)

    def __sub__(self, otro: "Dinero") -> "Dinero":
        return Dinero(max(self.monto - otro.monto, Decimal("0")), self.moneda)

    def por(self, cantidad: int) -> "Dinero":
        return Dinero(self.monto * cantidad, self.moneda)

    def porcentaje(self, porcentaje: Decimal) -> "Dinero":
        return Dinero((self.monto * porcentaje / Decimal("100")).quantize(Decimal("0.01")), self.moneda)


class Canal(Enum):
    MESA = "mesa"
    TELEFONO_WHATSAPP = "telefono_whatsapp"
    DOMICILIO = "domicilio"


class EstacionCocina(Enum):
    PARRILLA = "parrilla"
    FRIA = "fria"
    BEBIDAS = "bebidas"
    EMPAQUE = "empaque"


class Rol(Enum):
    MESERO = "mesero"
    CAJA = "caja"
    COCINA = "cocina"
    ENCARGADO = "encargado"
    REPARTIDOR = "repartidor"
    GERENTE = "gerente"
    CLIENTE = "cliente"


@dataclass(frozen=True)
class Responsable:
    """Usuario y rol que ejecuta una acción (RN-14, NEC-04)."""
    usuario_id: str
    rol: Rol


@dataclass(frozen=True)
class DatosCliente:
    nombre: str = ""
    telefono: str = ""
    direccion: str = ""


@dataclass(frozen=True)
class ProductoPedido:
    """Instantánea del producto al capturar el pedido (supuesto H-09)."""
    producto_id: str
    nombre: str
    precio_unitario: Dinero


@dataclass(frozen=True)
class Vigencia:
    """Días de la semana (0=lunes ... 6=domingo) y horario en que aplica una promoción."""
    dias: frozenset
    hora_inicio: time
    hora_fin: time

    def incluye(self, fecha_hora: datetime) -> bool:
        return fecha_hora.weekday() in self.dias and self.hora_inicio <= fecha_hora.time() <= self.hora_fin


@dataclass(frozen=True)
class PromocionAplicada:
    promocion_id: str
    descripcion: str
    descuento: Dinero


class TipoCancelacion(Enum):
    TOTAL = "total"
    PARCIAL = "parcial"  # quitar una línea (H-03)


@dataclass(frozen=True)
class Cancelacion:
    """Registro de trazabilidad: quién, por qué, con qué autorización (NEC-04, RN-03)."""
    tipo: TipoCancelacion
    motivo: str
    responsable: Responsable
    autorizado_por: Responsable | None
    fecha: datetime
