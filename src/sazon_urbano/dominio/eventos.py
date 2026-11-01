"""Domain Events: algo importante ya ocurrió (Etapa 3). Se nombran en pasado."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PedidoConfirmado:
    pedido_id: str


@dataclass(frozen=True)
class PromocionAplicadaAPedido:
    pedido_id: str
    promocion_id: str


@dataclass(frozen=True)
class PedidoCancelado:
    pedido_id: str
    requiere_merma: bool


@dataclass(frozen=True)
class LineaDePedidoCancelada:
    pedido_id: str
    linea_id: str


@dataclass(frozen=True)
class PedidoListo:
    pedido_id: str
    es_domicilio: bool


@dataclass(frozen=True)
class MermaRegistrada:
    merma_id: str
    pedido_id: str


@dataclass(frozen=True)
class ProductoMarcadoAgotado:
    producto_id: str


@dataclass(frozen=True)
class RepartidorAsignado:
    entrega_id: str
    pedido_id: str
    repartidor_id: str


@dataclass(frozen=True)
class EntregaIniciada:
    entrega_id: str


@dataclass(frozen=True)
class EntregaCompletada:
    entrega_id: str
    pedido_id: str


@dataclass(frozen=True)
class EntregaFallida:
    entrega_id: str
    pedido_id: str
    motivo: str
