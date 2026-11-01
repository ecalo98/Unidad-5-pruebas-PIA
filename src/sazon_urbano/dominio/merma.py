"""Aggregate Merma (delgado): nace de una cancelación autorizada con preparación iniciada (RN-03).
Una vez registrada no se edita (trazabilidad)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .valores import Cancelacion, Responsable


@dataclass(frozen=True)
class Merma:
    id: str
    pedido_id: str
    motivo: str
    responsable: Responsable
    fecha: datetime

    @classmethod
    def desde_cancelacion(cls, id: str, pedido_id: str, cancelacion: Cancelacion) -> "Merma":
        responsable = cancelacion.autorizado_por or cancelacion.responsable
        return cls(id, pedido_id, cancelacion.motivo, responsable, cancelacion.fecha)
