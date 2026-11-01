"""Raíz de composición: único lugar donde se conectan las interfaces con sus implementaciones."""
from __future__ import annotations

from dataclasses import dataclass

from sazon_urbano.aplicacion import handlers as h
from sazon_urbano.aplicacion.servicios import (
    DisponibilidadApplicationService,
    EntregaApplicationService,
    PedidoApplicationService,
)
from sazon_urbano.dominio.servicios import AplicadorDePromocion, AsignadorDeRepartidor

from .memoria import (
    ControlDeAccesoPorRol,
    DisponibilidadEnMemoria,
    EntregaRepositoryEnMemoria,
    MermaRepositoryEnMemoria,
    NotificadorInterno,
    PedidoRepositoryEnMemoria,
    PromocionRepositoryEnMemoria,
    PublicadorDeEventosEnMemoria,
    RepartidorRepositoryEnMemoria,
    UnitOfWorkEnMemoria,
)


@dataclass
class Aplicacion:
    pedidos_svc: PedidoApplicationService
    disponibilidad_svc: DisponibilidadApplicationService
    entregas_svc: EntregaApplicationService
    pedidos: PedidoRepositoryEnMemoria
    promociones: PromocionRepositoryEnMemoria
    entregas: EntregaRepositoryEnMemoria
    repartidores: RepartidorRepositoryEnMemoria
    mermas: MermaRepositoryEnMemoria
    disponibilidad: DisponibilidadEnMemoria
    publicador: PublicadorDeEventosEnMemoria
    notificador: NotificadorInterno


def construir_aplicacion() -> Aplicacion:
    pedidos, promociones = PedidoRepositoryEnMemoria(), PromocionRepositoryEnMemoria()
    entregas, repartidores = EntregaRepositoryEnMemoria(), RepartidorRepositoryEnMemoria()
    mermas, disponibilidad = MermaRepositoryEnMemoria(), DisponibilidadEnMemoria()
    uow = UnitOfWorkEnMemoria(pedidos, promociones, entregas, repartidores, mermas, disponibilidad)
    publicador, notificador, acceso = PublicadorDeEventosEnMemoria(), NotificadorInterno(), ControlDeAccesoPorRol()
    aplicador, asignador = AplicadorDePromocion(), AsignadorDeRepartidor()

    return Aplicacion(
        pedidos_svc=PedidoApplicationService(
            acceso,
            h.RegistrarPedidoHandler(pedidos, uow, publicador),
            h.AplicarPromocionHandler(pedidos, promociones, aplicador, uow, publicador),
            h.CancelarPedidoHandler(pedidos, mermas, uow, publicador),
        ),
        disponibilidad_svc=DisponibilidadApplicationService(
            acceso,
            h.MarcarProductoAgotadoHandler(disponibilidad, notificador, uow, publicador),
            h.QuitarLineaAgotadaHandler(pedidos, disponibilidad, uow, publicador),
        ),
        entregas_svc=EntregaApplicationService(
            acceso,
            h.AsignarRepartidorHandler(pedidos, repartidores, entregas, asignador, uow, publicador),
            h.RegistrarSalidaHandler(entregas, uow, publicador),
            h.ConfirmarEntregaHandler(entregas, pedidos, repartidores, uow, publicador),
            h.RegistrarEntregaFallidaHandler(entregas, pedidos, repartidores, uow, publicador),
        ),
        pedidos=pedidos, promociones=promociones, entregas=entregas, repartidores=repartidores,
        mermas=mermas, disponibilidad=disponibilidad, publicador=publicador, notificador=notificador,
    )
