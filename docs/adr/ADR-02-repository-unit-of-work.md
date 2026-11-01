# ADR-02: Repositorios con interfaz en el dominio y Unit of Work por solicitud

| Campo | Contenido |
|---|---|
| **Estado** | Aceptada |
| **Contexto** | El dominio no debe depender de SQL ni de la base de datos. La cancelación con preparación iniciada debe guardar `Pedido` y `Merma` juntos (RN-03). El BRD advierte que la red puede tener intermitencias. No hay base de datos real en este ejercicio. |
| **Alternativas** | **Servicios con SQL directo:** acopla el negocio a la tecnología. **Repository sin Unit of Work:** riesgo de guardar solo una parte de los cambios. **Repository + Unit of Work por solicitud:** más piezas, pero con atomicidad. |
| **Decisión** | Interfaces de Repository en el dominio (9 métodos en total) e implementaciones en infraestructura (en memoria para el código base). Una Unit of Work por solicitud: se confirma al final o se deshace todo, y los eventos se publican después de confirmar. No se implementa protección contra concurrencia, para mantener el diseño simple. |
| **Consecuencias** | **Beneficios:** se puede cambiar de tecnología sin tocar el negocio, y `cancelarPedido` nunca deja un pedido cancelado sin su merma. **Costos:** más interfaces. **Riesgos:** sin control de concurrencia, dos usuarios podrían actuar sobre un estado desactualizado; se acepta por ser un sistema ficticio de una sola base. **Trabajo posterior:** si pasara a producción, agregar control de versiones sobre el pedido. |
| **Trazabilidad** | NEC-01, NEC-04 · RN-03, RN-13 · Restricciones del BRD (red intermitente) · Hallazgos H4 y H5 de la revisión SOLID |
