import unittest

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.errores import AccesoDenegado, CancelacionRequiereAutorizacion, OperacionNoPermitidaEnEstado
from sazon_urbano.dominio.eventos import MermaRegistrada, PedidoCancelado
from sazon_urbano.dominio.pedido import EstadoPedido
from sazon_urbano.dominio.valores import EstacionCocina

from .escenario import CAJA, ENCARGADO, MESERO, nueva_aplicacion, registrar_mesa


class TestCancelarPedido(unittest.TestCase):
    """CU-03 (RN-02, RN-03)."""

    def setUp(self):
        self.app = nueva_aplicacion()
        self.pedido_id = registrar_mesa(self.app).pedido_id
        self.app.publicador.publicados.clear()

    def _iniciar_preparacion(self):
        pedido = self.app.pedidos.obtener_por_id(self.pedido_id)
        pedido.iniciar_preparacion(EstacionCocina.PARRILLA)
        self.app.pedidos.guardar(pedido)

    def _cancelar(self, solicitante=MESERO, autorizador=None):
        return self.app.pedidos_svc.cancelar_pedido(
            c.CancelarPedido(self.pedido_id, "El cliente cambió de opinión", solicitante, autorizador)
        )

    def test_sin_preparacion_se_cancela_directo_y_sin_merma(self):  # RN-02
        resultado = self._cancelar()
        pedido = self.app.pedidos.obtener_por_id(self.pedido_id)
        self.assertEqual(pedido.estado, EstadoPedido.CANCELADO)
        self.assertFalse(resultado.genero_merma)
        self.assertEqual(self.app.mermas.almacen, {})
        self.assertEqual(pedido.cancelaciones[0].responsable, MESERO)  # trazabilidad (NEC-04)

    def test_con_preparacion_sin_autorizacion_se_rechaza_y_no_se_guarda_nada(self):  # RN-03
        self._iniciar_preparacion()
        with self.assertRaises(CancelacionRequiereAutorizacion):
            self._cancelar()
        self.assertEqual(self.app.pedidos.obtener_por_id(self.pedido_id).estado, EstadoPedido.EN_PREPARACION)
        self.assertEqual(self.app.mermas.almacen, {})
        self.assertEqual(self.app.publicador.publicados, [])

    def test_con_preparacion_y_encargado_se_cancela_y_se_registra_la_merma(self):  # RN-03
        self._iniciar_preparacion()
        resultado = self._cancelar(autorizador=ENCARGADO)
        self.assertTrue(resultado.genero_merma)
        self.assertEqual(len(self.app.mermas.almacen), 1)
        tipos = [type(e) for e in self.app.publicador.publicados]
        self.assertIn(PedidoCancelado, tipos)
        self.assertIn(MermaRegistrada, tipos)

    def test_un_autorizador_que_no_es_encargado_no_sirve(self):
        self._iniciar_preparacion()
        with self.assertRaises(AccesoDenegado):  # solo el Encargado autoriza (RN-10)
            self._cancelar(autorizador=CAJA)
        self.assertEqual(self.app.mermas.almacen, {})

    def test_un_pedido_cancelado_no_se_puede_cancelar_otra_vez(self):
        self._cancelar()
        with self.assertRaises(OperacionNoPermitidaEnEstado):
            self._cancelar()

    def test_si_falla_el_guardado_de_la_merma_el_pedido_tampoco_queda_cancelado(self):
        """Unit of Work: Pedido y Merma se guardan juntos o no se guarda nada."""
        self._iniciar_preparacion()
        self.app.mermas.guardar = lambda merma: (_ for _ in ()).throw(RuntimeError("falla técnica"))
        # Se sustituye el método en la instancia que usa el handler.
        with self.assertRaises(RuntimeError):
            self._cancelar(autorizador=ENCARGADO)
        self.assertEqual(self.app.pedidos.obtener_por_id(self.pedido_id).estado, EstadoPedido.EN_PREPARACION)


if __name__ == "__main__":
    unittest.main()
