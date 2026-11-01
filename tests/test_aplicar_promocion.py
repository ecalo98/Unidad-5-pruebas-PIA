import unittest
from decimal import Decimal

from sazon_urbano.aplicacion import comandos as c
from sazon_urbano.dominio.errores import (
    AccesoDenegado,
    PedidoYaTienePromocion,
    PromocionFueraDeVigencia,
    PromocionNoEncontrada,
)

from .escenario import CAJA, MARTES_19H, MESERO, MIERCOLES_19H, nueva_aplicacion, registrar_mesa


class TestAplicarPromocion(unittest.TestCase):
    """CU-02 (RN-04, RN-05)."""

    def setUp(self):
        self.app = nueva_aplicacion()
        self.pedido_id = registrar_mesa(self.app).pedido_id  # 180 (tacos) + 30 (refresco) = 210

    def _aplicar(self, promocion_id, fecha_hora=MARTES_19H, responsable=CAJA):
        return self.app.pedidos_svc.aplicar_promocion(
            c.AplicarPromocion(self.pedido_id, promocion_id, fecha_hora, responsable)
        )

    def test_caja_aplica_promocion_vigente_y_se_recalcula_el_total(self):
        resultado = self._aplicar("promo-martes")  # 20 % de 180 = 36
        self.assertEqual(resultado.total.monto, Decimal("174"))

    def test_segunda_promocion_se_rechaza(self):  # RN-04
        self._aplicar("promo-martes")
        with self.assertRaises(PedidoYaTienePromocion):
            self._aplicar("promo-otra")

    def test_promocion_fuera_de_vigencia_se_rechaza(self):
        with self.assertRaises(PromocionFueraDeVigencia):
            self._aplicar("promo-martes", fecha_hora=MIERCOLES_19H)
        self.assertIsNone(self.app.pedidos.obtener_por_id(self.pedido_id).promocion)

    def test_el_mesero_no_aplica_promociones(self):  # el mesero no aplica descuentos
        with self.assertRaises(AccesoDenegado):
            self._aplicar("promo-martes", responsable=MESERO)

    def test_promocion_inexistente_lanza_error_de_negocio(self):  # contrato de repositorios (H4)
        with self.assertRaises(PromocionNoEncontrada):
            self._aplicar("no-existe")


if __name__ == "__main__":
    unittest.main()
