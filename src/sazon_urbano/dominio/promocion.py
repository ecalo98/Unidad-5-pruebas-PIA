"""Aggregate Promoción (Etapas 3 y 7). Sabe si aplica y calcula su propio descuento (hallazgo H3, principio O)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from .valores import Dinero, Vigencia


class Promocion:
    def __init__(self, id: str, nombre: str, vigencia: Vigencia, productos_ids, porcentaje_descuento):
        self.id = id
        self.nombre = nombre
        self.vigencia = vigencia
        self.productos_ids = frozenset(productos_ids)
        self.porcentaje_descuento = Decimal(str(porcentaje_descuento))

    def esta_vigente_en(self, fecha_hora: datetime) -> bool:
        return self.vigencia.incluye(fecha_hora)

    def aplica_a(self, pedido) -> bool:
        return any(l.producto.producto_id in self.productos_ids for l in pedido.lineas)

    def calcular_descuento(self, pedido) -> Dinero:
        """Descuento sobre las líneas elegibles. Un tipo nuevo de promoción (2x1, por monto...)
        se agrega como variante de esta clase, sin tocar Pedido ni los servicios."""
        base = Dinero.cero()
        for linea in pedido.lineas:
            if linea.producto.producto_id in self.productos_ids:
                base = base + linea.subtotal
        return base.porcentaje(self.porcentaje_descuento)
