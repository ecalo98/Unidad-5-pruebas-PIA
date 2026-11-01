# ADR-01: Domain Model como patrón de lógica de negocio

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada |
| **Contexto** | Sazón Urbano maneja 15 reglas de negocio, 6 roles y 3 canales de pedido. Varias reglas dependen del estado del pedido por estación (RN-02, RN-03, RN-12) y deben aplicarse igual sin importar el canal. Las promociones cambian con frecuencia (por ejemplo, el 2x1 de martes que hoy se aplica "de memoria"). |
| **Alternativas** | **Transaction Script:** rápido de construir, pero duplicaría las reglas en cada flujo y cada cambio tocaría varios scripts. **Table Module:** muy bueno para reportes, pero no modela el ciclo de vida del pedido. **Domain Model:** reglas y estado juntos, a costa de más estructura inicial. |
| **Decisión** | Domain Model como patrón principal. Transaction Script solo en CU-04a (marcar agotado), por ser una operación lineal. Table Module descartado en los 5 casos de uso. |
| **Consecuencias** | **Beneficios:** una regla vive en un solo lugar y los cambios quedan localizados. **Costos:** más clases y estructura que con scripts. **Riesgos:** `Pedido` concentra mucho comportamiento. **Trabajo posterior:** los reportes (US-13 y US-17) podrían usar Table Module. |
| **Trazabilidad** | NEC-04, NEC-05, NEC-11, NEC-12 · RN-01 a RN-06, RN-12, RN-14 · US-03, 05, 06, 07, 08, 09, 18 · CU-01 a CU-05 |
