"""Domain Services: reglas que involucran a más de un aggregate (Etapa 3)."""
from __future__ import annotations

from datetime import datetime

from .entrega import Entrega
from .errores import PromocionFueraDeVigencia, PromocionNoAplicable
from .pedido import Pedido
from .promocion import Promocion
from .repartidor import Repartidor
from .valores import PromocionAplicada


class AplicadorDePromocion:
    """Verifica vigencia y productos, pide a la Promoción su descuento y luego el Pedido
    impone la no acumulación (RN-04)."""

    def aplicar(self, pedido: Pedido, promocion: Promocion, fecha_hora: datetime) -> None:
        if not promocion.esta_vigente_en(fecha_hora):
            raise PromocionFueraDeVigencia(promocion.nombre)
        if not promocion.aplica_a(pedido):
            raise PromocionNoAplicable(promocion.nombre)
        descuento = promocion.calcular_descuento(pedido)
        pedido.aplicar_promocion(PromocionAplicada(promocion.id, promocion.nombre, descuento))


class AsignadorDeRepartidor:
    """Verifica la disponibilidad del repartidor y crea la entrega.
    La cercanía la decide el Encargado; no se automatiza para no inventar una regla."""

    def asignar(self, entrega_id: str, pedido_id: str, repartidor: Repartidor) -> Entrega:
        repartidor.asignar()
        return Entrega.asignar(entrega_id, pedido_id, repartidor.id)
