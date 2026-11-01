"""Commands: solicitudes que cambian el estado del sistema (Etapa 6)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sazon_urbano.dominio.valores import Canal, DatosCliente, EstacionCocina, Responsable


@dataclass(frozen=True)
class LineaSolicitada:
    producto_id: str
    nombre: str
    precio: Decimal
    cantidad: int
    estacion: EstacionCocina
    modificaciones: tuple = ()


@dataclass(frozen=True)
class RegistrarPedido:
    canal: Canal
    lineas: list
    responsable: Responsable
    cliente: DatosCliente | None = None
    mesa: str | None = None


@dataclass(frozen=True)
class AplicarPromocion:
    pedido_id: str
    promocion_id: str
    fecha_hora: datetime
    responsable: Responsable


@dataclass(frozen=True)
class CancelarPedido:
    pedido_id: str
    motivo: str
    solicitante: Responsable
    autorizador: Responsable | None = None


@dataclass(frozen=True)
class MarcarProductoAgotado:
    producto_id: str
    responsable: Responsable
    fecha_hora: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class QuitarLineaAgotada:
    pedido_id: str
    linea_id: str
    responsable: Responsable


@dataclass(frozen=True)
class AsignarRepartidor:
    pedido_id: str
    repartidor_id: str
    responsable: Responsable


@dataclass(frozen=True)
class RegistrarSalidaDeEntrega:
    entrega_id: str
    responsable: Responsable
    hora: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ConfirmarEntrega:
    entrega_id: str
    responsable: Responsable
    hora: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class RegistrarEntregaFallida:
    entrega_id: str
    motivo: str
    responsable: Responsable
    hora: datetime = field(default_factory=datetime.now)
