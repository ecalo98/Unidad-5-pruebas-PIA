"""Application Services (Etapa 4): puerta de entrada de cada caso de uso.
Verifican permisos y entregan el Command a su Handler. Solo coordinan."""
from __future__ import annotations

from sazon_urbano.dominio.valores import Canal

from . import comandos as c
from .puertos import Accion, ControlDeAcceso


class PedidoApplicationService:
    def __init__(self, acceso: ControlDeAcceso, registrar, aplicar_promocion, cancelar):
        self._acceso = acceso
        self._registrar, self._aplicar, self._cancelar = registrar, aplicar_promocion, cancelar

    def registrar_pedido(self, cmd: c.RegistrarPedido):  # CU-01
        accion = Accion.REGISTRAR_PEDIDO_MESA if cmd.canal is Canal.MESA else Accion.REGISTRAR_PEDIDO_REMOTO
        self._acceso.verificar_permiso(cmd.responsable, accion)
        return self._registrar.manejar(cmd)

    def aplicar_promocion(self, cmd: c.AplicarPromocion):  # CU-02
        self._acceso.verificar_permiso(cmd.responsable, Accion.APLICAR_PROMOCION)
        return self._aplicar.manejar(cmd)

    def cancelar_pedido(self, cmd: c.CancelarPedido):  # CU-03
        self._acceso.verificar_permiso(cmd.solicitante, Accion.SOLICITAR_CANCELACION)
        if cmd.autorizador is not None:
            self._acceso.verificar_permiso(cmd.autorizador, Accion.AUTORIZAR_CANCELACION)
        return self._cancelar.manejar(cmd)


class DisponibilidadApplicationService:
    def __init__(self, acceso: ControlDeAcceso, marcar_agotado, quitar_linea):
        self._acceso = acceso
        self._rutas = {
            c.MarcarProductoAgotado: (Accion.MARCAR_AGOTADO, marcar_agotado),
            c.QuitarLineaAgotada: (Accion.QUITAR_LINEA_AGOTADA, quitar_linea),
        }

    def gestionar_producto_agotado(self, solicitud):  # CU-04 (enruta; no decide reglas)
        accion, handler = self._rutas[type(solicitud)]
        self._acceso.verificar_permiso(solicitud.responsable, accion)
        return handler.manejar(solicitud)


class EntregaApplicationService:
    def __init__(self, acceso: ControlDeAcceso, asignar, salida, confirmar, fallida):
        self._acceso = acceso
        self._rutas = {
            c.AsignarRepartidor: (Accion.ASIGNAR_REPARTIDOR, asignar),
            c.RegistrarSalidaDeEntrega: (Accion.REGISTRAR_ENTREGA, salida),
            c.ConfirmarEntrega: (Accion.REGISTRAR_ENTREGA, confirmar),
            c.RegistrarEntregaFallida: (Accion.REGISTRAR_ENTREGA, fallida),
        }

    def gestionar_entrega(self, solicitud):  # CU-05 (enruta; no decide reglas)
        accion, handler = self._rutas[type(solicitud)]
        self._acceso.verificar_permiso(solicitud.responsable, accion)
        return handler.manejar(solicitud)
