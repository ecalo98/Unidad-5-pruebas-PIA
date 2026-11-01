"""Aggregate Repartidor (delgado): conoce su disponibilidad."""
from .errores import RepartidorNoDisponible


class Repartidor:
    def __init__(self, id: str, nombre: str, disponible: bool = True):
        self.id = id
        self.nombre = nombre
        self.disponible = disponible

    def asignar(self):
        if not self.disponible:
            raise RepartidorNoDisponible(self.nombre)
        self.disponible = False

    def liberar(self):
        # Supuesto: queda disponible al cerrar la entrega, completada o fallida.
        self.disponible = True
