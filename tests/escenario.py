"""Datos y utilidades comunes de las pruebas."""
from datetime import datetime, time
from decimal import Decimal

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.promocion import Promocion
from sazon_urbano.dominio.repartidor import Repartidor
from sazon_urbano.dominio.valores import Canal, DatosCliente, EstacionCocina, Responsable, Rol, Vigencia
from sazon_urbano.infraestructura.composicion import construir_aplicacion

MESERO = Responsable("ana", Rol.MESERO)
CAJA = Responsable("luis", Rol.CAJA)
COCINA = Responsable("coc1", Rol.COCINA)
ENCARGADO = Responsable("eva", Rol.ENCARGADO)
REPARTIDOR = Responsable("rep1", Rol.REPARTIDOR)
CLIENTE = Responsable("cli", Rol.CLIENTE)

MARTES_19H = datetime(2026, 10, 13, 19, 0)   # martes
MIERCOLES_19H = datetime(2026, 10, 14, 19, 0)  # miércoles

TACOS = c.LineaSolicitada("taco-pastor", "Tacos al pastor", Decimal("90"), 2, EstacionCocina.PARRILLA)  # 180
REFRESCO = c.LineaSolicitada("refresco", "Refresco", Decimal("30"), 1, EstacionCocina.BEBIDAS)  # 30
AGUA = c.LineaSolicitada("agua", "Agua", Decimal("20"), 1, EstacionCocina.BEBIDAS)  # 20
CLIENTE_DOMICILIO = DatosCliente("Marta", "8112345678", "Calle 1 #100")


def nueva_aplicacion():
    app = construir_aplicacion()
    app.promociones.guardar(
        Promocion("promo-martes", "Martes de tacos", Vigencia(frozenset({1}), time(18), time(21)), {"taco-pastor"}, 20)
    )
    app.promociones.guardar(
        Promocion("promo-otra", "Otra promoción", Vigencia(frozenset({1}), time(18), time(21)), {"taco-pastor"}, 10)
    )
    app.repartidores.guardar(Repartidor("rep-1", "Pedro"))
    return app


def registrar_mesa(app, lineas=None):
    return app.pedidos_svc.registrar_pedido(
        c.RegistrarPedido(Canal.MESA, lineas or [TACOS, REFRESCO], MESERO, mesa="5")
    )


def registrar_domicilio(app, lineas=None):
    return app.pedidos_svc.registrar_pedido(
        c.RegistrarPedido(Canal.DOMICILIO, lineas or [TACOS], CAJA, cliente=CLIENTE_DOMICILIO)
    )


def pedido_listo_a_domicilio(app):
    """Deja un pedido a domicilio en estado LISTO (el flujo de cocina queda fuera de los 5 casos)."""
    resultado = registrar_domicilio(app)
    pedido = app.pedidos.obtener_por_id(resultado.pedido_id)
    pedido.marcar_listo()
    app.pedidos.guardar(pedido)
    return resultado.pedido_id
