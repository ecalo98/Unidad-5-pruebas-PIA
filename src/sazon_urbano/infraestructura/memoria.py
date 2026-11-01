"""Implementaciones en memoria de las interfaces del dominio y la aplicación.
Son las que usa el código base (la empresa es ficticia y no hay base de datos real).
Una implementación relacional cumpliría las mismas interfaces sin tocar el dominio."""
from __future__ import annotations

import copy

from sazon_urbano.aplicacion.puertos import (
    Accion,
    ConsultasDeDisponibilidad,
    ControlDeAcceso,
    Notificador,
    PublicadorDeEventos,
)
from sazon_urbano.dominio.errores import (
    AccesoDenegado,
    EntregaNoEncontrada,
    PedidoNoEncontrado,
    PromocionNoEncontrada,
    RepartidorNoEncontrado,
)
from sazon_urbano.dominio.repositorios import (
    DisponibilidadRepository,
    EntregaRepository,
    MermaRepository,
    PedidoRepository,
    PromocionRepository,
    RepartidorRepository,
    UnitOfWork,
)
from sazon_urbano.dominio.valores import Rol


class _RepositorioEnMemoria:
    _error = None

    def __init__(self):
        self.almacen: dict = {}

    def obtener_por_id(self, id):
        if id not in self.almacen:
            raise self._error(id)  # contrato común: siempre un error de negocio (H4)
        return copy.deepcopy(self.almacen[id])

    def guardar(self, objeto):
        self.almacen[objeto.id] = copy.deepcopy(objeto)


class PedidoRepositoryEnMemoria(_RepositorioEnMemoria, PedidoRepository):
    _error = PedidoNoEncontrado


class PromocionRepositoryEnMemoria(_RepositorioEnMemoria, PromocionRepository):
    _error = PromocionNoEncontrada


class EntregaRepositoryEnMemoria(_RepositorioEnMemoria, EntregaRepository):
    _error = EntregaNoEncontrada


class RepartidorRepositoryEnMemoria(_RepositorioEnMemoria, RepartidorRepository):
    _error = RepartidorNoEncontrado


class MermaRepositoryEnMemoria(_RepositorioEnMemoria, MermaRepository):
    pass


class DisponibilidadEnMemoria(DisponibilidadRepository, ConsultasDeDisponibilidad):
    """Implementa la escritura y la lectura por separado (cada consumidor usa solo su interfaz)."""

    def __init__(self):
        self.almacen: dict = {}  # producto_id -> agotado

    def marcar_agotado(self, producto_id, responsable, fecha_hora):
        self.almacen[producto_id] = True

    def esta_agotado(self, producto_id) -> bool:
        return self.almacen.get(producto_id, False)


class UnitOfWorkEnMemoria(UnitOfWork):
    """Toma una instantánea al iniciar y la restaura si se deshace."""

    def __init__(self, *repositorios):
        self._repositorios = repositorios
        self._instantanea = None

    def iniciar(self):
        self._instantanea = [copy.deepcopy(r.almacen) for r in self._repositorios]

    def confirmar(self):
        self._instantanea = None

    def deshacer(self):
        if self._instantanea is not None:
            for repositorio, copia in zip(self._repositorios, self._instantanea):
                repositorio.almacen.clear()
                repositorio.almacen.update(copia)
        self._instantanea = None


class PublicadorDeEventosEnMemoria(PublicadorDeEventos):
    def __init__(self):
        self.publicados: list = []

    def publicar(self, eventos: list) -> None:
        self.publicados.extend(eventos)


class NotificadorInterno(Notificador):
    def __init__(self):
        self.mensajes: list = []

    def avisar(self, destinatarios: list, mensaje: str) -> None:
        self.mensajes.append((tuple(destinatarios), mensaje))


class ControlDeAccesoPorRol(ControlDeAcceso):
    """Tabla de permisos por rol de la matriz de trazabilidad (US-19, NEC-10)."""

    PERMISOS = {
        Accion.REGISTRAR_PEDIDO_MESA: {Rol.MESERO},
        Accion.REGISTRAR_PEDIDO_REMOTO: {Rol.CAJA},
        Accion.APLICAR_PROMOCION: {Rol.CAJA},
        Accion.SOLICITAR_CANCELACION: {Rol.MESERO, Rol.CAJA},
        Accion.AUTORIZAR_CANCELACION: {Rol.ENCARGADO},
        Accion.MARCAR_AGOTADO: {Rol.COCINA},
        Accion.QUITAR_LINEA_AGOTADA: {Rol.MESERO},
        Accion.ASIGNAR_REPARTIDOR: {Rol.ENCARGADO},
        Accion.REGISTRAR_ENTREGA: {Rol.REPARTIDOR},
    }

    def verificar_permiso(self, responsable, accion):
        if responsable.rol not in self.PERMISOS.get(accion, set()):
            raise AccesoDenegado(f"El rol {responsable.rol.value} no puede {accion.value}")
