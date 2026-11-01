import unittest
from decimal import Decimal

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.errores import AccesoDenegado, ProductoNoEstaAgotado
from sazon_urbano.dominio.eventos import LineaDePedidoCancelada, ProductoMarcadoAgotado
from sazon_urbano.dominio.valores import TipoCancelacion

from .escenario import CAJA, COCINA, MESERO, nueva_aplicacion, registrar_mesa


class TestProductoAgotado(unittest.TestCase):
    """CU-04 (RN-06)."""

    def setUp(self):
        self.app = nueva_aplicacion()
        self.pedido_id = registrar_mesa(self.app).pedido_id  # tacos 180 + refresco 30
        self.pedido = self.app.pedidos.obtener_por_id(self.pedido_id)
        self.linea_tacos = next(l for l in self.pedido.lineas if l.producto.producto_id == "taco-pastor")
        self.app.publicador.publicados.clear()

    def _marcar(self, producto_id, responsable=COCINA):
        return self.app.disponibilidad_svc.gestionar_producto_agotado(c.MarcarProductoAgotado(producto_id, responsable))

    def _quitar(self, linea_id, responsable=MESERO):
        return self.app.disponibilidad_svc.gestionar_producto_agotado(
            c.QuitarLineaAgotada(self.pedido_id, linea_id, responsable)
        )

    def test_cocina_marca_agotado_y_se_avisa_a_mesero_y_caja(self):  # 4a, Transaction Script
        self._marcar("taco-pastor")
        self.assertTrue(self.app.disponibilidad.esta_agotado("taco-pastor"))
        self.assertEqual(self.app.notificador.mensajes[0][0], ("mesero", "caja"))
        self.assertEqual(self.app.publicador.publicados, [ProductoMarcadoAgotado("taco-pastor")])

    def test_solo_cocina_marca_agotado(self):
        with self.assertRaises(AccesoDenegado):
            self._marcar("taco-pastor", responsable=CAJA)
        self.assertEqual(self.app.notificador.mensajes, [])

    def test_mesero_quita_la_linea_agotada_sin_cancelar_el_pedido(self):  # 4b, RN-06
        self._marcar("taco-pastor")
        resultado = self._quitar(self.linea_tacos.id)
        pedido = self.app.pedidos.obtener_por_id(self.pedido_id)
        self.assertEqual(resultado.estado, "confirmado")           # el pedido sigue
        self.assertEqual(resultado.total.monto, Decimal("30"))     # total recalculado
        self.assertEqual(pedido.cancelaciones[-1].tipo, TipoCancelacion.PARCIAL)
        self.assertIn(LineaDePedidoCancelada(self.pedido_id, self.linea_tacos.id), self.app.publicador.publicados)

    def test_no_se_quita_una_linea_cuyo_producto_no_esta_agotado(self):
        with self.assertRaises(ProductoNoEstaAgotado):
            self._quitar(self.linea_tacos.id)
        self.assertEqual(len(self.app.pedidos.obtener_por_id(self.pedido_id).lineas), 2)


if __name__ == "__main__":
    unittest.main()
