import unittest
from decimal import Decimal

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.errores import AccesoDenegado, DatosDeDomicilioIncompletos, MontoMinimoDomicilioNoAlcanzado
from sazon_urbano.dominio.eventos import PedidoConfirmado
from sazon_urbano.dominio.valores import Canal, DatosCliente

from .escenario import AGUA, CAJA, CLIENTE_DOMICILIO, MESERO, TACOS, nueva_aplicacion, registrar_domicilio, registrar_mesa


class TestRegistrarPedido(unittest.TestCase):
    """CU-01 (RN-01, RN-14)."""

    def setUp(self):
        self.app = nueva_aplicacion()

    def test_pedido_en_mesa_se_confirma_con_responsable_y_canal(self):
        resultado = registrar_mesa(self.app)
        pedido = self.app.pedidos.obtener_por_id(resultado.pedido_id)
        self.assertEqual(resultado.estado, "confirmado")
        self.assertEqual(pedido.responsable, MESERO)          # RN-14
        self.assertEqual(pedido.canal, Canal.MESA)            # RN-14
        self.assertEqual(resultado.total.monto, Decimal("210"))
        self.assertEqual(self.app.publicador.publicados, [PedidoConfirmado(pedido.id)])

    def test_domicilio_que_cumple_el_minimo_se_confirma(self):
        resultado = registrar_domicilio(self.app)  # 180 MXN
        self.assertEqual(resultado.estado, "confirmado")

    def test_domicilio_menor_a_150_se_rechaza_y_no_se_guarda_ni_publica_nada(self):  # RN-01
        with self.assertRaises(MontoMinimoDomicilioNoAlcanzado) as ctx:
            registrar_domicilio(self.app, [AGUA])  # 20 MXN
        self.assertEqual(ctx.exception.faltante.monto, Decimal("130"))
        self.assertEqual(self.app.pedidos.almacen, {})
        self.assertEqual(self.app.publicador.publicados, [])

    def test_domicilio_sin_direccion_ni_telefono_se_rechaza(self):  # US-02
        with self.assertRaises(DatosDeDomicilioIncompletos):
            self.app.pedidos_svc.registrar_pedido(
                c.RegistrarPedido(Canal.DOMICILIO, [TACOS], CAJA, cliente=DatosCliente("Marta"))
            )

    def test_mesero_no_puede_registrar_pedidos_a_domicilio(self):  # H-01 / permisos
        with self.assertRaises(AccesoDenegado):
            self.app.pedidos_svc.registrar_pedido(
                c.RegistrarPedido(Canal.DOMICILIO, [TACOS], MESERO, cliente=CLIENTE_DOMICILIO)
            )


if __name__ == "__main__":
    unittest.main()
