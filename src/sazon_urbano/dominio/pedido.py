"""Aggregate Pedido: raíz, líneas y preparación por estación (Etapa 3).

Aquí viven RN-01, RN-02, RN-03, RN-04, RN-06, RN-12 y RN-14. Ninguna otra capa
decide estas reglas: solo piden al Pedido que actúe.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .errores import (
    CancelacionRequiereAutorizacion,
    DatosDeDomicilioIncompletos,
    LineaNoExiste,
    MontoMinimoDomicilioNoAlcanzado,
    OperacionNoPermitidaEnEstado,
    PedidoNoEsADomicilio,
    PedidoNoEstaListo,
    PedidoYaTienePromocion,
    ProductoNoEstaAgotado,
)
from .eventos import (
    LineaDePedidoCancelada,
    PedidoCancelado,
    PedidoConfirmado,
    PedidoListo,
    PromocionAplicadaAPedido,
)
from .valores import (
    Canal,
    Cancelacion,
    DatosCliente,
    Dinero,
    EstacionCocina,
    ProductoPedido,
    PromocionAplicada,
    Responsable,
    Rol,
    TipoCancelacion,
)


class EstadoPedido(Enum):
    """Estados derivados del BPMN (supuesto H-12)."""
    CAPTURADO = "capturado"
    CONFIRMADO = "confirmado"
    EN_PREPARACION = "en_preparacion"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    ENTREGA_NO_COMPLETADA = "entrega_no_completada"


class EstadoPreparacion(Enum):
    PENDIENTE = "pendiente"
    EN_PREPARACION = "en_preparacion"
    TERMINADA = "terminada"


@dataclass
class LineaPedido:
    id: str
    producto: ProductoPedido
    cantidad: int
    estacion: EstacionCocina  # estación que prepara la línea (supuesto: la define el producto)
    modificaciones: tuple = ()

    @property
    def subtotal(self) -> Dinero:
        return self.producto.precio_unitario.por(self.cantidad)


@dataclass
class PreparacionEstacion:
    estacion: EstacionCocina
    estado: EstadoPreparacion = EstadoPreparacion.PENDIENTE


_ESTADOS_FINALES = (
    EstadoPedido.CANCELADO,
    EstadoPedido.ENTREGADO,
    EstadoPedido.ENTREGA_NO_COMPLETADA,
)


class Pedido:
    MONTO_MINIMO_DOMICILIO = Dinero.mxn(150)  # RN-01

    def __init__(self, id, canal, responsable, lineas, cliente, mesa):
        self.id = id
        self.canal = canal
        self.responsable = responsable  # RN-14
        self.lineas = list(lineas)
        self.cliente = cliente
        self.mesa = mesa
        self.estado = EstadoPedido.CAPTURADO
        self.preparaciones: dict = {}
        self.promocion: PromocionAplicada | None = None
        self.cancelaciones: list = []
        self._eventos: list = []

    # -- creación ------------------------------------------------------------
    @classmethod
    def crear(cls, id, canal: Canal, responsable: Responsable, lineas, cliente: DatosCliente | None = None, mesa=None):
        if canal is Canal.DOMICILIO and (cliente is None or not cliente.telefono or not cliente.direccion):
            raise DatosDeDomicilioIncompletos("El domicilio exige teléfono y dirección")
        return cls(id, canal, responsable, lineas, cliente, mesa)

    # -- consultas internas --------------------------------------------------
    @property
    def subtotal(self) -> Dinero:
        total = Dinero.cero()
        for linea in self.lineas:
            total = total + linea.subtotal
        return total

    @property
    def total(self) -> Dinero:
        descuento = self.promocion.descuento if self.promocion else Dinero.cero()
        return self.subtotal - descuento

    @property
    def preparacion_iniciada(self) -> bool:
        return any(p.estado is not EstadoPreparacion.PENDIENTE for p in self.preparaciones.values())

    def _exigir_no_final(self):
        if self.estado in _ESTADOS_FINALES:
            raise OperacionNoPermitidaEnEstado(f"El pedido está {self.estado.value}")

    # -- comportamiento (casos de uso) ---------------------------------------
    def confirmar(self):
        """CU-01. RN-01: domicilio con total menor al mínimo no se confirma."""
        if self.estado is not EstadoPedido.CAPTURADO:
            raise OperacionNoPermitidaEnEstado("Solo se confirma un pedido capturado")
        if self.canal is Canal.DOMICILIO and self.total < self.MONTO_MINIMO_DOMICILIO:
            raise MontoMinimoDomicilioNoAlcanzado(self.MONTO_MINIMO_DOMICILIO - self.total)
        for linea in self.lineas:
            self.preparaciones.setdefault(linea.estacion, PreparacionEstacion(linea.estacion))
        self.estado = EstadoPedido.CONFIRMADO
        self._eventos.append(PedidoConfirmado(self.id))

    def aplicar_promocion(self, promocion: PromocionAplicada):
        """CU-02. RN-04: una sola promoción por pedido."""
        self._exigir_no_final()
        if self.promocion is not None:
            raise PedidoYaTienePromocion("Las promociones no son acumulables")
        self.promocion = promocion
        self._eventos.append(PromocionAplicadaAPedido(self.id, promocion.promocion_id))

    def cancelar(self, solicitante: Responsable, motivo: str, autorizador: Responsable | None = None):
        """CU-03. RN-02: sin preparación iniciada se cancela directo.
        RN-03: con preparación iniciada exige al Encargado y genera merma."""
        self._exigir_no_final()
        preparacion_iniciada = self.preparacion_iniciada
        if preparacion_iniciada and (autorizador is None or autorizador.rol is not Rol.ENCARGADO):
            raise CancelacionRequiereAutorizacion("Se requiere la autorización del Encargado")
        self.cancelaciones.append(
            Cancelacion(TipoCancelacion.TOTAL, motivo, solicitante, autorizador, datetime.now())
        )
        self.estado = EstadoPedido.CANCELADO
        self._eventos.append(PedidoCancelado(self.id, requiere_merma=preparacion_iniciada))

    def quitar_linea(self, linea_id: str, producto_agotado: bool, responsable: Responsable):
        """CU-04b. RN-06 (cancelación parcial). Supuesto H-08: RN-06 prevalece sobre RN-12
        cuando el producto está agotado."""
        self._exigir_no_final()
        linea = next((l for l in self.lineas if l.id == linea_id), None)
        if linea is None:
            raise LineaNoExiste(linea_id)
        if not producto_agotado:
            raise ProductoNoEstaAgotado(linea.producto.nombre)
        self.lineas.remove(linea)
        self.cancelaciones.append(
            Cancelacion(TipoCancelacion.PARCIAL, "Producto agotado", responsable, None, datetime.now())
        )
        self._eventos.append(LineaDePedidoCancelada(self.id, linea_id))

    # -- avance de preparación (flujo de cocina, fuera de los 5 casos) --------
    def iniciar_preparacion(self, estacion: EstacionCocina):
        self._exigir_no_final()
        self.preparaciones[estacion].estado = EstadoPreparacion.EN_PREPARACION
        self.estado = EstadoPedido.EN_PREPARACION

    def marcar_listo(self):
        if self.estado not in (EstadoPedido.CONFIRMADO, EstadoPedido.EN_PREPARACION):
            raise OperacionNoPermitidaEnEstado("Solo se marca listo un pedido confirmado o en preparación")
        for preparacion in self.preparaciones.values():
            preparacion.estado = EstadoPreparacion.TERMINADA
        self.estado = EstadoPedido.LISTO
        self._eventos.append(PedidoListo(self.id, self.canal is Canal.DOMICILIO))

    # -- cierre por entrega (CU-05) ------------------------------------------
    def validar_entrega_a_domicilio(self):
        if self.canal is not Canal.DOMICILIO:
            raise PedidoNoEsADomicilio(self.id)
        if self.estado is not EstadoPedido.LISTO:
            raise PedidoNoEstaListo(self.id)

    def marcar_entregado(self):
        if self.estado is not EstadoPedido.LISTO:
            raise OperacionNoPermitidaEnEstado("Solo se entrega un pedido listo")
        self.estado = EstadoPedido.ENTREGADO

    def marcar_entrega_no_completada(self):
        if self.estado is not EstadoPedido.LISTO:
            raise OperacionNoPermitidaEnEstado("Solo falla la entrega de un pedido listo")
        self.estado = EstadoPedido.ENTREGA_NO_COMPLETADA

    # -- eventos -------------------------------------------------------------
    def recoger_eventos(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos
