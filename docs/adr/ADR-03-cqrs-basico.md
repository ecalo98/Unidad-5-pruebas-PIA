# ADR-03: CQRS básico con Handlers, DTO de lectura y una sola base de datos

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada |
| **Contexto** | Hay operaciones que cambian el estado (registrar, cancelar, asignar) y necesidades de solo lectura (resumen del pedido, menú disponible, promociones vigentes, repartidores disponibles). US-04 pide que lo agotado "deje de mostrarse" sin meter una regla extra al registrar pedidos. La guía no exige bases de datos separadas. |
| **Alternativas** | **Un solo modelo para leer y escribir:** expondría el aggregate `Pedido` a pantallas y mezclaría responsabilidades. **CQRS completo con bases separadas:** complejidad que un restaurante único no justifica. **CQRS básico:** separación en el código, una sola base. |
| **Decisión** | 9 Commands y 4 Queries, cada uno con su Handler. Las consultas dependen de interfaces de lectura y devuelven DTO, nunca el aggregate. Una sola base de datos. |
| **Consecuencias** | **Beneficios:** responsabilidades claras, lecturas con el modelo adecuado y cumplimiento del principio I de SOLID. **Costos:** más clases (un handler por operación). **Riesgos:** duplicar conceptos entre el DTO y el aggregate. **Trabajo posterior:** los reportes pesados podrían separarse más adelante. |
| **Trazabilidad** | NEC-03, NEC-08, NEC-09 · RN-05 · US-04, US-13, US-17 · Hallazgo H6 |
