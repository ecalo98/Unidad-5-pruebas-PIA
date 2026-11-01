"""Handlers de Commands: aquí vive la coordinación de cada caso de uso (Etapas 4 y 6).
No contienen reglas de negocio: piden al dominio que actúe, guardan y publican."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sazon_urbano.dominio.eventos import MermaRegistrada, ProductoMarcadoAgotado
from sazon_urbano.dominio.merma import Merma
from sazon_urbano.dominio.pedido import LineaPedido, Pedido
from sazon_urbano.dominio.repositorios import (
    DisponibilidadRepository,
    EntregaRepository,
    MermaRepository,
    PedidoRepository,
    PromocionRepository,
    RepartidorRepository,
    UnitOfWork,
)
from sazon_urbano.dominio.servicios import AplicadorDePromocion, AsignadorDeRepartidor
from sazon_urbano.dominio.valores import Dinero, ProductoPedido

from . import comandos as c
from .puertos import ConsultasDeDisponibilidad, Notificador, PublicadorDeEventos


@dataclass(frozen=True)
class ResultadoPedido:
    pedido_id: str
    total: Dinero
    estado: str
    genero_merma: bool = False


@dataclass(frozen=True)
class ResultadoEntrega:
    entrega_id: str
    estado: str


@dataclass(frozen=True)
class ResultadoDisponibilidad:
    producto_id: str
    agotado: bool = True


def _en_unidad_de_trabajo(uow: UnitOfWork, publicador: PublicadorDeEventos, operacion):
    """Inicio y fin transaccional de cada solicitud (Etapa 5).
    Si algo falla se deshace todo y NO se publica ningún evento."""
    uow.iniciar()
    try:
        resultado, eventos = operacion()
        uow.confirmar()
    except Exception:
        uow.deshacer()
        raise
    publicador.publicar(eventos)  # los eventos se publican DESPUÉS de confirmar
    return resultado


class RegistrarPedidoHandler:
    def __init__(self, pedidos: PedidoRepository, uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._pedidos, self._uow, self._publicador = pedidos, uow, publicador

    def manejar(self, cmd: c.RegistrarPedido) -> ResultadoPedido:
        def operacion():
            lineas = [
                LineaPedido(
                    id=uuid4().hex[:8],
                    producto=ProductoPedido(l.producto_id, l.nombre, Dinero.mxn(l.precio)),
                    cantidad=l.cantidad,
                    estacion=l.estacion,
                    modificaciones=l.modificaciones,
                )
                for l in cmd.lineas
            ]
            pedido = Pedido.crear(uuid4().hex[:8], cmd.canal, cmd.responsable, lineas, cmd.cliente, cmd.mesa)
            pedido.confirmar()  # aquí el dominio aplica RN-01 y RN-14
            eventos = pedido.recoger_eventos()
            self._pedidos.guardar(pedido)
            return ResultadoPedido(pedido.id, pedido.total, pedido.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class AplicarPromocionHandler:
    def __init__(self, pedidos: PedidoRepository, promociones: PromocionRepository,
                 aplicador: AplicadorDePromocion, uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._pedidos, self._promociones, self._aplicador = pedidos, promociones, aplicador
        self._uow, self._publicador = uow, publicador

    def manejar(self, cmd: c.AplicarPromocion) -> ResultadoPedido:
        def operacion():
            pedido = self._pedidos.obtener_por_id(cmd.pedido_id)
            promocion = self._promociones.obtener_por_id(cmd.promocion_id)
            self._aplicador.aplicar(pedido, promocion, cmd.fecha_hora)
            eventos = pedido.recoger_eventos()
            self._pedidos.guardar(pedido)
            return ResultadoPedido(pedido.id, pedido.total, pedido.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class CancelarPedidoHandler:
    def __init__(self, pedidos: PedidoRepository, mermas: MermaRepository,
                 uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._pedidos, self._mermas, self._uow, self._publicador = pedidos, mermas, uow, publicador

    def manejar(self, cmd: c.CancelarPedido) -> ResultadoPedido:
        def operacion():
            pedido = self._pedidos.obtener_por_id(cmd.pedido_id)
            pedido.cancelar(cmd.solicitante, cmd.motivo, cmd.autorizador)  # RN-02 y RN-03 en el dominio
            eventos = pedido.recoger_eventos()
            genero_merma = any(getattr(e, "requiere_merma", False) for e in eventos)
            if genero_merma:
                merma = Merma.desde_cancelacion(uuid4().hex[:8], pedido.id, pedido.cancelaciones[-1])
                self._mermas.guardar(merma)  # Pedido y Merma se guardan juntos
                eventos.append(MermaRegistrada(merma.id, pedido.id))
            self._pedidos.guardar(pedido)
            return ResultadoPedido(pedido.id, pedido.total, pedido.estado.value, genero_merma), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class MarcarProductoAgotadoHandler:
    """Transaction Script (CU-04a): operación lineal sin regla compleja (ADR-01)."""

    def __init__(self, disponibilidad: DisponibilidadRepository, notificador: Notificador,
                 uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._disponibilidad, self._notificador = disponibilidad, notificador
        self._uow, self._publicador = uow, publicador

    def manejar(self, cmd: c.MarcarProductoAgotado) -> ResultadoDisponibilidad:
        def operacion():
            self._disponibilidad.marcar_agotado(cmd.producto_id, cmd.responsable, cmd.fecha_hora)
            return ResultadoDisponibilidad(cmd.producto_id), [ProductoMarcadoAgotado(cmd.producto_id)]

        resultado = _en_unidad_de_trabajo(self._uow, self._publicador, operacion)
        # El aviso se envía solo si todo quedó guardado (Etapa 5).
        self._notificador.avisar(["mesero", "caja"], f"Producto agotado: {cmd.producto_id}")
        return resultado


class QuitarLineaAgotadaHandler:
    def __init__(self, pedidos: PedidoRepository, consultas: ConsultasDeDisponibilidad,
                 uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._pedidos, self._consultas, self._uow, self._publicador = pedidos, consultas, uow, publicador

    def manejar(self, cmd: c.QuitarLineaAgotada) -> ResultadoPedido:
        def operacion():
            pedido = self._pedidos.obtener_por_id(cmd.pedido_id)
            linea = next((l for l in pedido.lineas if l.id == cmd.linea_id), None)
            # El handler solo CONSULTA el dato; la decisión la toma el Pedido (RN-06).
            agotado = self._consultas.esta_agotado(linea.producto.producto_id) if linea else False
            pedido.quitar_linea(cmd.linea_id, agotado, cmd.responsable)
            eventos = pedido.recoger_eventos()
            self._pedidos.guardar(pedido)
            return ResultadoPedido(pedido.id, pedido.total, pedido.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class AsignarRepartidorHandler:
    def __init__(self, pedidos: PedidoRepository, repartidores: RepartidorRepository,
                 entregas: EntregaRepository, asignador: AsignadorDeRepartidor,
                 uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._pedidos, self._repartidores, self._entregas = pedidos, repartidores, entregas
        self._asignador, self._uow, self._publicador = asignador, uow, publicador

    def manejar(self, cmd: c.AsignarRepartidor) -> ResultadoEntrega:
        def operacion():
            pedido = self._pedidos.obtener_por_id(cmd.pedido_id)
            pedido.validar_entrega_a_domicilio()
            repartidor = self._repartidores.obtener_por_id(cmd.repartidor_id)
            entrega = self._asignador.asignar(uuid4().hex[:8], pedido.id, repartidor)
            eventos = entrega.recoger_eventos()
            self._entregas.guardar(entrega)
            self._repartidores.guardar(repartidor)
            return ResultadoEntrega(entrega.id, entrega.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class RegistrarSalidaHandler:
    def __init__(self, entregas: EntregaRepository, uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._entregas, self._uow, self._publicador = entregas, uow, publicador

    def manejar(self, cmd: c.RegistrarSalidaDeEntrega) -> ResultadoEntrega:
        def operacion():
            entrega = self._entregas.obtener_por_id(cmd.entrega_id)
            entrega.registrar_salida(cmd.hora)
            eventos = entrega.recoger_eventos()
            self._entregas.guardar(entrega)
            return ResultadoEntrega(entrega.id, entrega.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class _CierreDeEntregaHandler:
    """Entrega, Pedido y Repartidor se guardan juntos (Etapa 5, ajuste a la Etapa 4)."""

    def __init__(self, entregas: EntregaRepository, pedidos: PedidoRepository,
                 repartidores: RepartidorRepository, uow: UnitOfWork, publicador: PublicadorDeEventos):
        self._entregas, self._pedidos, self._repartidores = entregas, pedidos, repartidores
        self._uow, self._publicador = uow, publicador

    def _cerrar(self, cmd, accion_entrega, accion_pedido) -> ResultadoEntrega:
        def operacion():
            entrega = self._entregas.obtener_por_id(cmd.entrega_id)
            accion_entrega(entrega)
            pedido = self._pedidos.obtener_por_id(entrega.pedido_id)
            accion_pedido(pedido)
            repartidor = self._repartidores.obtener_por_id(entrega.repartidor_id)
            repartidor.liberar()
            eventos = entrega.recoger_eventos()
            self._entregas.guardar(entrega)
            self._pedidos.guardar(pedido)
            self._repartidores.guardar(repartidor)
            return ResultadoEntrega(entrega.id, entrega.estado.value), eventos

        return _en_unidad_de_trabajo(self._uow, self._publicador, operacion)


class ConfirmarEntregaHandler(_CierreDeEntregaHandler):
    def manejar(self, cmd: c.ConfirmarEntrega) -> ResultadoEntrega:
        return self._cerrar(cmd, lambda e: e.confirmar(cmd.hora), lambda p: p.marcar_entregado())


class RegistrarEntregaFallidaHandler(_CierreDeEntregaHandler):
    def manejar(self, cmd: c.RegistrarEntregaFallida) -> ResultadoEntrega:
        return self._cerrar(
            cmd, lambda e: e.fallar(cmd.motivo, cmd.hora), lambda p: p.marcar_entrega_no_completada()
        )
