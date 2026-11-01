"""Aggregate Entrega: ciclo de vida de una entrega a domicilio (RN-11)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from .errores import EntregaSinSalidaRegistrada, MotivoDeFallaObligatorio, OperacionNoPermitidaEnEstado
from .eventos import EntregaCompletada, EntregaFallida, EntregaIniciada, RepartidorAsignado


class EstadoEntrega(Enum):
    ASIGNADA = "asignada"
    EN_RUTA = "en_ruta"
    ENTREGADA = "entregada"
    FALLIDA = "fallida"


class Entrega:
    def __init__(self, id: str, pedido_id: str, repartidor_id: str):
        self.id = id
        self.pedido_id = pedido_id
        self.repartidor_id = repartidor_id
        self.estado = EstadoEntrega.ASIGNADA
        self.hora_salida: datetime | None = None
        self.hora_entrega: datetime | None = None
        self.motivo_falla: str | None = None
        self._eventos: list = []

    @classmethod
    def asignar(cls, id: str, pedido_id: str, repartidor_id: str) -> "Entrega":
        entrega = cls(id, pedido_id, repartidor_id)
        entrega._eventos.append(RepartidorAsignado(id, pedido_id, repartidor_id))
        return entrega

    def registrar_salida(self, hora: datetime):
        if self.estado is not EstadoEntrega.ASIGNADA:
            raise OperacionNoPermitidaEnEstado("La salida solo se registra en una entrega asignada")
        self.hora_salida = hora
        self.estado = EstadoEntrega.EN_RUTA
        self._eventos.append(EntregaIniciada(self.id))

    def confirmar(self, hora: datetime):
        if self.estado is not EstadoEntrega.EN_RUTA:
            raise EntregaSinSalidaRegistrada("No se puede entregar sin registrar la salida (RN-11)")
        self.hora_entrega = hora
        self.estado = EstadoEntrega.ENTREGADA
        self._eventos.append(EntregaCompletada(self.id, self.pedido_id))

    def fallar(self, motivo: str, hora: datetime):
        if not motivo or not motivo.strip():
            raise MotivoDeFallaObligatorio("Una entrega fallida exige motivo (RN-11)")
        if self.estado is not EstadoEntrega.EN_RUTA:
            raise EntregaSinSalidaRegistrada("No se puede fallar sin registrar la salida (RN-11)")
        self.hora_entrega = hora
        self.motivo_falla = motivo
        self.estado = EstadoEntrega.FALLIDA
        self._eventos.append(EntregaFallida(self.id, self.pedido_id, motivo))

    def recoger_eventos(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos
