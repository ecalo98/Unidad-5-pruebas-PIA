"""Interfaces de Repository y Unit of Work. Viven en el dominio y hablan en términos del negocio.
Las implementaciones están en infraestructura.

Contrato común (H4): obtener_por_id SIEMPRE lanza un error de negocio si el objeto no existe.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .entrega import Entrega
from .merma import Merma
from .pedido import Pedido
from .promocion import Promocion
from .repartidor import Repartidor
from .valores import Responsable


class PedidoRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, pedido_id: str) -> Pedido: ...

    @abstractmethod
    def guardar(self, pedido: Pedido) -> None: ...


class PromocionRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, promocion_id: str) -> Promocion: ...


class EntregaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, entrega_id: str) -> Entrega: ...

    @abstractmethod
    def guardar(self, entrega: Entrega) -> None: ...


class RepartidorRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, repartidor_id: str) -> Repartidor: ...

    @abstractmethod
    def guardar(self, repartidor: Repartidor) -> None: ...


class MermaRepository(ABC):
    @abstractmethod
    def guardar(self, merma: Merma) -> None: ...


class DisponibilidadRepository(ABC):
    """Solo escritura (H5). La consulta esta_agotado vive en ConsultasDeDisponibilidad."""

    @abstractmethod
    def marcar_agotado(self, producto_id: str, responsable: Responsable, fecha_hora: datetime) -> None: ...


class UnitOfWork(ABC):
    """Una unidad de trabajo por solicitud: se confirma todo junto o se deshace todo."""

    @abstractmethod
    def iniciar(self) -> None: ...

    @abstractmethod
    def confirmar(self) -> None: ...

    @abstractmethod
    def deshacer(self) -> None: ...
