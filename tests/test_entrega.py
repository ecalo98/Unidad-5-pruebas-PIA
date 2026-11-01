import unittest

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.errores import (
    EntregaSinSalidaRegistrada,
    MotivoDeFallaObligatorio,
    PedidoNoEsADomicilio,
    PedidoNoEstaListo,
    RepartidorNoDisponible,
)
from sazon_urbano.dominio.pedido import EstadoPedido

from .escenario import ENCARGADO, REPARTIDOR, nueva_aplicacion, pedido_listo_a_domicilio, registrar_domicilio, registrar_mesa


class TestEntrega(unittest.TestCase):
    """CU-05 (RN-11)."""

    def setUp(self):
        self.app = nueva_aplicacion()
        self.pedido_id = pedido_listo_a_domicilio(self.app)

    def _asignar(self, pedido_id=None):
        return self.app.entregas_svc.gestionar_entrega(
            c.AsignarRepartidor(pedido_id or self.pedido_id, "rep-1", ENCARGADO)
        )

    def _gestionar(self, solicitud):
        return self.app.entregas_svc.gestionar_entrega(solicitud)

    def test_flujo_completo_asignar_salir_y_entregar(self):
        entrega_id = self._asignar().entrega_id
        self.assertFalse(self.app.repartidores.obtener_por_id("rep-1").disponible)
        self._gestionar(c.RegistrarSalidaDeEntrega(entrega_id, REPARTIDOR))
        resultado = self._gestionar(c.ConfirmarEntrega(entrega_id, REPARTIDOR))
        self.assertEqual(resultado.estado, "entregada")
        self.assertEqual(self.app.pedidos.obtener_por_id(self.pedido_id).estado, EstadoPedido.ENTREGADO)
        self.assertTrue(self.app.repartidores.obtener_por_id("rep-1").disponible)  # supuesto: queda libre

    def test_entrega_fallida_exige_motivo_y_cierra_el_pedido_como_no_completado(self):
        entrega_id = self._asignar().entrega_id
        self._gestionar(c.RegistrarSalidaDeEntrega(entrega_id, REPARTIDOR))
        with self.assertRaises(MotivoDeFallaObligatorio):
            self._gestionar(c.RegistrarEntregaFallida(entrega_id, "  ", REPARTIDOR))
        self._gestionar(c.RegistrarEntregaFallida(entrega_id, "Cliente ausente", REPARTIDOR))
        self.assertEqual(
            self.app.pedidos.obtener_por_id(self.pedido_id).estado, EstadoPedido.ENTREGA_NO_COMPLETADA
        )

    def test_no_se_entrega_sin_registrar_la_salida(self):  # RN-11
        entrega_id = self._asignar().entrega_id
        with self.assertRaises(EntregaSinSalidaRegistrada):
            self._gestionar(c.ConfirmarEntrega(entrega_id, REPARTIDOR))
        self.assertEqual(self.app.pedidos.obtener_por_id(self.pedido_id).estado, EstadoPedido.LISTO)

    def test_no_se_asigna_un_repartidor_no_disponible(self):
        self._asignar()
        otro_pedido = pedido_listo_a_domicilio(self.app)
        with self.assertRaises(RepartidorNoDisponible):
            self._asignar(otro_pedido)

    def test_solo_los_pedidos_a_domicilio_tienen_entrega(self):
        pedido_mesa = registrar_mesa(self.app).pedido_id
        with self.assertRaises(PedidoNoEsADomicilio):
            self._asignar(pedido_mesa)

    def test_el_pedido_debe_estar_listo_para_asignar_repartidor(self):
        pedido_sin_terminar = registrar_domicilio(self.app).pedido_id
        with self.assertRaises(PedidoNoEstaListo):
            self._asignar(pedido_sin_terminar)


if __name__ == "__main__":
    unittest.main()
