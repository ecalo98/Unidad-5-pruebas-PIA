"""Errores de negocio. Sus nombres usan el lenguaje ubicuo del glosario (Etapas 3 y 4)."""


class ErrorDeNegocio(Exception):
    """Base de todos los errores que el negocio entiende (no son fallas técnicas)."""


# --- Pedido -----------------------------------------------------------------
class MontoMinimoDomicilioNoAlcanzado(ErrorDeNegocio):
    """RN-01: un pedido a domicilio exige un mínimo de 150 MXN."""

    def __init__(self, faltante):
        super().__init__(f"Faltan {faltante.monto} {faltante.moneda} para el monto mínimo de domicilio")
        self.faltante = faltante


class DatosDeDomicilioIncompletos(ErrorDeNegocio):
    """US-02: el domicilio exige teléfono y dirección."""


class PedidoYaTienePromocion(ErrorDeNegocio):
    """RN-04: las promociones no son acumulables."""


class CancelacionRequiereAutorizacion(ErrorDeNegocio):
    """RN-03: con preparación iniciada, cancelar exige autorización del Encargado."""


class LineaNoExiste(ErrorDeNegocio):
    pass


class ProductoNoEstaAgotado(ErrorDeNegocio):
    pass


class OperacionNoPermitidaEnEstado(ErrorDeNegocio):
    """La operación no es válida para el estado actual del objeto."""


# --- Promoción --------------------------------------------------------------
class PromocionFueraDeVigencia(ErrorDeNegocio):
    pass


class PromocionNoAplicable(ErrorDeNegocio):
    pass


# --- Entrega ----------------------------------------------------------------
class PedidoNoEsADomicilio(ErrorDeNegocio):
    pass


class PedidoNoEstaListo(ErrorDeNegocio):
    pass


class RepartidorNoDisponible(ErrorDeNegocio):
    pass


class EntregaSinSalidaRegistrada(ErrorDeNegocio):
    """RN-11: no se registra la entrega sin hora de salida."""


class MotivoDeFallaObligatorio(ErrorDeNegocio):
    """RN-11: una entrega fallida exige motivo."""


# --- Contrato común de los repositorios (hallazgo H4 de SOLID) --------------
class PedidoNoEncontrado(ErrorDeNegocio):
    pass


class PromocionNoEncontrada(ErrorDeNegocio):
    pass


class EntregaNoEncontrada(ErrorDeNegocio):
    pass


class RepartidorNoEncontrado(ErrorDeNegocio):
    pass


# --- Permisos (capa de aplicación) ------------------------------------------
class AccesoDenegado(ErrorDeNegocio):
    """US-19: el rol no tiene permiso para la acción."""
