"""Puertos de la capa de aplicación: interfaces que la infraestructura implementa."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from sazon_urbano.dominio.valores import Responsable


class Accion(Enum):
    REGISTRAR_PEDIDO_MESA = "registrar_pedido_mesa"
    REGISTRAR_PEDIDO_REMOTO = "registrar_pedido_remoto"  # teléfono, WhatsApp o domicilio
    APLICAR_PROMOCION = "aplicar_promocion"
    SOLICITAR_CANCELACION = "solicitar_cancelacion"
    AUTORIZAR_CANCELACION = "autorizar_cancelacion"
    MARCAR_AGOTADO = "marcar_agotado"
    QUITAR_LINEA_AGOTADA = "quitar_linea_agotada"
    ASIGNAR_REPARTIDOR = "asignar_repartidor"
    REGISTRAR_ENTREGA = "registrar_entrega"  # salida, entrega o entrega fallida


class ControlDeAcceso(ABC):
    @abstractmethod
    def verificar_permiso(self, responsable: Responsable, accion: Accion) -> None:
        """Lanza AccesoDenegado si el rol no puede ejecutar la acción (US-19)."""


class PublicadorDeEventos(ABC):
    @abstractmethod
    def publicar(self, eventos: list) -> None: ...


class Notificador(ABC):
    @abstractmethod
    def avisar(self, destinatarios: list, mensaje: str) -> None: ...


class ConsultasDeDisponibilidad(ABC):
    """Interfaz de lectura (H5): quien solo consulta no depende de métodos de escritura."""

    @abstractmethod
    def esta_agotado(self, producto_id: str) -> bool: ...
