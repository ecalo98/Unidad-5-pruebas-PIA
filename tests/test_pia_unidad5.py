"""Pruebas de la Unidad 5 para Sazón Urbano (PIA). Se verifica el código tal como quedó en la Unidad 3.

Reglas elegidas: RN-01 (monto mínimo a domicilio), RN-04 con vigencia de promociones (NEC-05),
RN-02/RN-03 (cancelación) y RN-11 (registro de entrega), más persistencia (Unit of Work)
y un servicio externo simulado (Notificador). Cada caso está en tests/matriz_pia.py (PIA-01 a PIA-21).
Patrón de cada prueba: Arrange (preparar) - Act (ejecutar) - Assert (verificar).
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.aplicacion.handlers import MarcarProductoAgotadoHandler
from sazon_urbano.aplicacion.puertos import Notificador
from sazon_urbano.dominio.errores import (
    CancelacionRequiereAutorizacion,
    EntregaSinSalidaRegistrada,
    MontoMinimoDomicilioNoAlcanzado,
    MotivoDeFallaObligatorio,
    PedidoYaTienePromocion,
    PromocionFueraDeVigencia,
)
from sazon_urbano.dominio.eventos import MermaRegistrada, PedidoCancelado, PedidoConfirmado
from sazon_urbano.dominio.pedido import EstadoPedido
from sazon_urbano.dominio.valores import Canal, EstacionCocina
from sazon_urbano.infraestructura.memoria import (
    DisponibilidadEnMemoria,
    PedidoRepositoryEnMemoria,
    PublicadorDeEventosEnMemoria,
    UnitOfWorkEnMemoria,
)

from .escenario import (
    AGUA,
    CAJA,
    COCINA,
    ENCARGADO,
    MARTES_19H,
    MESERO,
    REPARTIDOR,
    nueva_aplicacion,
    pedido_listo_a_domicilio,
    registrar_domicilio,
    registrar_mesa,
)
from .matriz_pia import observar

ENTRE_SEMANA_21H = datetime(2026, 10, 13, 21, 0)  # martes, hora final de la promoción
ENTRE_SEMANA_21H01 = datetime(2026, 10, 13, 21, 1)


@pytest.fixture
def app():
    return nueva_aplicacion()


def linea(producto_id, nombre, precio, cantidad, estacion):
    return c.LineaSolicitada(producto_id, nombre, Decimal(precio), cantidad, estacion)


# --------------------------------------------------------------------------------------
# RN-01: pedido a domicilio con monto mínimo de 150 MXN
# --------------------------------------------------------------------------------------
def test_pia_01_domicilio_sobre_el_minimo_se_confirma(app):
    resultado = registrar_domicilio(app)  # 2 tacos x 90 = 180 MXN
    observar("PIA-01", f"estado={resultado.estado}, total={resultado.total.monto}")
    assert resultado.estado == "confirmado"
    assert resultado.total.monto == Decimal("180")


def test_pia_02_domicilio_bajo_el_minimo_se_rechaza(app):
    with pytest.raises(MontoMinimoDomicilioNoAlcanzado) as error:
        registrar_domicilio(app, [AGUA])  # 20 MXN
    observar("PIA-02", f"MontoMinimoDomicilioNoAlcanzado (faltan {error.value.faltante.monto}); "
                       f"pedidos guardados={len(app.pedidos.almacen)}, eventos={len(app.publicador.publicados)}")
    assert error.value.faltante.monto == Decimal("130")
    assert app.pedidos.almacen == {}
    assert app.publicador.publicados == []


def test_pia_03_domicilio_de_exactamente_150_se_confirma(app):
    exacto = linea("refresco", "Refresco", "30", 5, EstacionCocina.BEBIDAS)  # 5 x 30 = 150.00
    resultado = registrar_domicilio(app, [exacto])
    observar("PIA-03", f"estado={resultado.estado}, total={resultado.total.monto}")
    assert resultado.estado == "confirmado"
    assert resultado.total.monto == Decimal("150")


def test_pia_04_domicilio_de_149_99_se_rechaza(app):
    casi = linea("especial", "Platillo especial", "149.99", 1, EstacionCocina.PARRILLA)
    with pytest.raises(MontoMinimoDomicilioNoAlcanzado) as error:
        registrar_domicilio(app, [casi])
    observar("PIA-04", f"MontoMinimoDomicilioNoAlcanzado (faltan {error.value.faltante.monto})")
    assert error.value.faltante.monto == Decimal("0.01")


# --------------------------------------------------------------------------------------
# RN-04 (una sola promoción por pedido) y NEC-05 (vigencia)
# --------------------------------------------------------------------------------------
def _aplicar(app, pedido_id, promocion_id, fecha_hora=MARTES_19H):
    return app.pedidos_svc.aplicar_promocion(c.AplicarPromocion(pedido_id, promocion_id, fecha_hora, CAJA))


def test_pia_05_promocion_vigente_recalcula_el_total(app):
    pedido_id = registrar_mesa(app).pedido_id  # 180 + 30 = 210 MXN
    resultado = _aplicar(app, pedido_id, "promo-martes")
    descuento = app.pedidos.obtener_por_id(pedido_id).promocion.descuento.monto
    observar("PIA-05", f"descuento={descuento}, total={resultado.total.monto}")
    assert descuento == Decimal("36.00")  # 20 % de 180 (solo la línea elegible)
    assert resultado.total.monto == Decimal("174")


def test_pia_06_segunda_promocion_se_rechaza(app):
    pedido_id = registrar_mesa(app).pedido_id
    _aplicar(app, pedido_id, "promo-martes")
    with pytest.raises(PedidoYaTienePromocion):
        _aplicar(app, pedido_id, "promo-otra")
    conservada = app.pedidos.obtener_por_id(pedido_id).promocion.promocion_id
    observar("PIA-06", f"PedidoYaTienePromocion; promoción conservada={conservada}")
    assert conservada == "promo-martes"


def test_pia_07_promocion_en_la_hora_exacta_de_fin_se_aplica(app):
    pedido_id = registrar_mesa(app).pedido_id
    resultado = _aplicar(app, pedido_id, "promo-martes", ENTRE_SEMANA_21H)
    observar("PIA-07", f"aplicada a las 21:00, total={resultado.total.monto}")
    assert resultado.total.monto == Decimal("174")


def test_pia_08_promocion_un_minuto_despues_del_fin_se_rechaza(app):
    pedido_id = registrar_mesa(app).pedido_id
    with pytest.raises(PromocionFueraDeVigencia):
        _aplicar(app, pedido_id, "promo-martes", ENTRE_SEMANA_21H01)
    promocion = app.pedidos.obtener_por_id(pedido_id).promocion
    observar("PIA-08", f"PromocionFueraDeVigencia; promoción del pedido={promocion}")
    assert promocion is None


# --------------------------------------------------------------------------------------
# RN-02 y RN-03: cancelación (con o sin preparación iniciada)
# --------------------------------------------------------------------------------------
def _iniciar_preparacion(app, pedido_id, estacion=EstacionCocina.PARRILLA):
    pedido = app.pedidos.obtener_por_id(pedido_id)
    pedido.iniciar_preparacion(estacion)
    app.pedidos.guardar(pedido)


def _cancelar(app, pedido_id, solicitante=MESERO, autorizador=None):
    return app.pedidos_svc.cancelar_pedido(
        c.CancelarPedido(pedido_id, "El cliente cambió de opinión", solicitante, autorizador)
    )


def test_pia_09_cancelacion_sin_preparacion_no_genera_merma(app):
    pedido_id = registrar_mesa(app).pedido_id
    resultado = _cancelar(app, pedido_id)
    pedido = app.pedidos.obtener_por_id(pedido_id)
    observar("PIA-09", f"estado={pedido.estado.value}, mermas={len(app.mermas.almacen)}, "
                       f"responsable={pedido.cancelaciones[0].responsable.usuario_id}")
    assert pedido.estado is EstadoPedido.CANCELADO
    assert resultado.genero_merma is False
    assert app.mermas.almacen == {}
    assert pedido.cancelaciones[0].motivo == "El cliente cambió de opinión"  # trazabilidad (NEC-04)


def test_pia_10_cancelacion_con_preparacion_exige_al_encargado(app):
    pedido_id = registrar_mesa(app).pedido_id
    _iniciar_preparacion(app, pedido_id)
    with pytest.raises(CancelacionRequiereAutorizacion):
        _cancelar(app, pedido_id)
    estado = app.pedidos.obtener_por_id(pedido_id).estado
    observar("PIA-10", f"CancelacionRequiereAutorizacion; estado={estado.value}, mermas={len(app.mermas.almacen)}")
    assert estado is EstadoPedido.EN_PREPARACION
    assert app.mermas.almacen == {}


def test_pia_11_basta_una_estacion_iniciada_para_exigir_autorizacion(app):
    pedido_id = registrar_mesa(app).pedido_id  # tacos (parrilla) + refresco (bebidas)
    _iniciar_preparacion(app, pedido_id, EstacionCocina.PARRILLA)  # bebidas sigue pendiente
    pedido = app.pedidos.obtener_por_id(pedido_id)
    pendientes = [p.estado.value for p in pedido.preparaciones.values()]
    with pytest.raises(CancelacionRequiereAutorizacion):
        _cancelar(app, pedido_id, solicitante=CAJA)
    observar("PIA-11", f"estaciones={sorted(pendientes)}; CancelacionRequiereAutorizacion con 1 de 2 iniciadas")
    assert sorted(pendientes) == ["en_preparacion", "pendiente"]


def test_pia_12_cancelacion_autorizada_registra_la_merma(app):
    pedido_id = registrar_mesa(app).pedido_id
    _iniciar_preparacion(app, pedido_id)
    app.publicador.publicados.clear()
    resultado = _cancelar(app, pedido_id, autorizador=ENCARGADO)
    tipos = {type(e) for e in app.publicador.publicados}
    observar("PIA-12", f"estado={app.pedidos.obtener_por_id(pedido_id).estado.value}, "
                       f"mermas={len(app.mermas.almacen)}, eventos={sorted(t.__name__ for t in tipos)}")
    assert resultado.genero_merma is True
    assert len(app.mermas.almacen) == 1
    assert {PedidoCancelado, MermaRegistrada} <= tipos


# --------------------------------------------------------------------------------------
# RN-11: el repartidor registra salida y entrega (o el motivo de la falla)
# --------------------------------------------------------------------------------------
def _asignar(app, pedido_id):
    return app.entregas_svc.gestionar_entrega(c.AsignarRepartidor(pedido_id, "rep-1", ENCARGADO)).entrega_id


def test_pia_13_entrega_registra_salida_y_entrega(app):
    pedido_id = pedido_listo_a_domicilio(app)
    entrega_id = _asignar(app, pedido_id)
    salida, entrega = datetime(2026, 10, 13, 19, 10), datetime(2026, 10, 13, 19, 35)
    app.entregas_svc.gestionar_entrega(c.RegistrarSalidaDeEntrega(entrega_id, REPARTIDOR, salida))
    resultado = app.entregas_svc.gestionar_entrega(c.ConfirmarEntrega(entrega_id, REPARTIDOR, entrega))
    guardada = app.entregas.obtener_por_id(entrega_id)
    observar("PIA-13", f"entrega={resultado.estado}, salida={guardada.hora_salida:%H:%M}, "
                       f"entrega={guardada.hora_entrega:%H:%M}, pedido={app.pedidos.obtener_por_id(pedido_id).estado.value}")
    assert resultado.estado == "entregada"
    assert (guardada.hora_salida, guardada.hora_entrega) == (salida, entrega)
    assert app.pedidos.obtener_por_id(pedido_id).estado is EstadoPedido.ENTREGADO


def test_pia_14_no_se_entrega_sin_salida_registrada(app):
    pedido_id = pedido_listo_a_domicilio(app)
    entrega_id = _asignar(app, pedido_id)
    with pytest.raises(EntregaSinSalidaRegistrada):
        app.entregas_svc.gestionar_entrega(c.ConfirmarEntrega(entrega_id, REPARTIDOR))
    estado = app.pedidos.obtener_por_id(pedido_id).estado
    observar("PIA-14", f"EntregaSinSalidaRegistrada; pedido={estado.value}")
    assert estado is EstadoPedido.LISTO


def test_pia_15_entrega_fallida_con_motivo_en_blanco_se_rechaza(app):
    pedido_id = pedido_listo_a_domicilio(app)
    entrega_id = _asignar(app, pedido_id)
    app.entregas_svc.gestionar_entrega(c.RegistrarSalidaDeEntrega(entrega_id, REPARTIDOR))
    with pytest.raises(MotivoDeFallaObligatorio):
        app.entregas_svc.gestionar_entrega(c.RegistrarEntregaFallida(entrega_id, "   ", REPARTIDOR))
    estado = app.entregas.obtener_por_id(entrega_id).estado
    observar("PIA-15", f"MotivoDeFallaObligatorio; entrega={estado.value}")
    assert estado.value == "en_ruta"


# --------------------------------------------------------------------------------------
# Persistencia: repositorios + Unit of Work (commit y rollback)
# --------------------------------------------------------------------------------------
def test_pia_16_pedido_confirmado_queda_guardado(app):
    resultado = registrar_mesa(app)
    guardado = app.pedidos.obtener_por_id(resultado.pedido_id)
    observar("PIA-16", f"id={guardado.id}, estado={guardado.estado.value}, responsable={guardado.responsable.usuario_id}, "
                       f"canal={guardado.canal.value}")
    assert guardado.estado is EstadoPedido.CONFIRMADO
    assert guardado.responsable == MESERO  # RN-14
    assert guardado.canal is Canal.MESA  # RN-14
    assert app.publicador.publicados == [PedidoConfirmado(guardado.id)]  # evento solo después del commit


def test_pia_17_falla_al_guardar_deshace_toda_la_operacion(app, monkeypatch):
    pedido_id = registrar_mesa(app).pedido_id
    _iniciar_preparacion(app, pedido_id)
    app.publicador.publicados.clear()

    def guardado_con_falla(merma):
        raise RuntimeError("falla técnica")

    monkeypatch.setattr(app.mermas, "guardar", guardado_con_falla)
    with pytest.raises(RuntimeError):
        _cancelar(app, pedido_id, autorizador=ENCARGADO)
    estado = app.pedidos.obtener_por_id(pedido_id).estado
    observar("PIA-17", f"RuntimeError; estado={estado.value}, mermas={len(app.mermas.almacen)}, "
                       f"eventos={len(app.publicador.publicados)}")
    assert estado is EstadoPedido.EN_PREPARACION
    assert app.mermas.almacen == {}
    assert app.publicador.publicados == []


def test_pia_18_deshacer_restaura_la_version_anterior(app):
    pedido_id = registrar_mesa(app).pedido_id
    repositorio = PedidoRepositoryEnMemoria()
    repositorio.guardar(app.pedidos.obtener_por_id(pedido_id))
    uow = UnitOfWorkEnMemoria(repositorio)

    uow.iniciar()
    pedido = repositorio.obtener_por_id(pedido_id)
    pedido.cancelar(MESERO, "prueba")
    repositorio.guardar(pedido)
    durante = repositorio.obtener_por_id(pedido_id).estado
    uow.deshacer()
    despues = repositorio.obtener_por_id(pedido_id).estado

    observar("PIA-18", f"durante la unidad de trabajo={durante.value}; después de deshacer={despues.value}")
    assert durante is EstadoPedido.CANCELADO
    assert despues is EstadoPedido.CONFIRMADO


# --------------------------------------------------------------------------------------
# Servicio externo simulado: el Notificador (no hay integraciones externas reales en el alcance del BRD)
# --------------------------------------------------------------------------------------
def _handler_agotado(notificador, disponibilidad=None):
    disponibilidad = disponibilidad or DisponibilidadEnMemoria()
    uow = UnitOfWorkEnMemoria(disponibilidad)
    return MarcarProductoAgotadoHandler(disponibilidad, notificador, uow, PublicadorDeEventosEnMemoria()), disponibilidad


def test_pia_19_se_avisa_a_mesero_y_caja_cuando_se_agota_un_producto():
    notificador = Mock(spec=Notificador)  # no se envía ningún mensaje real
    handler, disponibilidad = _handler_agotado(notificador)
    handler.manejar(c.MarcarProductoAgotado("agua", COCINA))
    observar("PIA-19", f"avisar llamado {notificador.avisar.call_count} vez con {notificador.avisar.call_args.args}")
    notificador.avisar.assert_called_once_with(["mesero", "caja"], "Producto agotado: agua")
    assert disponibilidad.esta_agotado("agua") is True


def test_pia_20_si_no_se_guarda_no_se_avisa():
    notificador = Mock(spec=Notificador)
    disponibilidad = Mock(spec=DisponibilidadEnMemoria)
    disponibilidad.marcar_agotado.side_effect = RuntimeError("falla técnica")
    disponibilidad.almacen = {}
    handler, _ = _handler_agotado(notificador, disponibilidad)
    with pytest.raises(RuntimeError):
        handler.manejar(c.MarcarProductoAgotado("agua", COCINA))
    observar("PIA-20", f"RuntimeError; avisar llamado {notificador.avisar.call_count} veces")
    notificador.avisar.assert_not_called()


def test_pia_21_si_el_aviso_falla_el_producto_ya_quedo_agotado():
    notificador = Mock(spec=Notificador)
    notificador.avisar.side_effect = TimeoutError("el notificador no responde")
    handler, disponibilidad = _handler_agotado(notificador)
    with pytest.raises(TimeoutError):
        handler.manejar(c.MarcarProductoAgotado("agua", COCINA))
    observar("PIA-21", f"TimeoutError al avisar; esta_agotado('agua')={disponibilidad.esta_agotado('agua')}")
    assert disponibilidad.esta_agotado("agua") is True  # el guardado ya se había confirmado
