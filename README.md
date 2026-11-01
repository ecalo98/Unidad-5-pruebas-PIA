# Sazón Urbano: diseño arquitectónico del sistema

Actividad práctica de la **Unidad 3** del curso *Componentes de Lógica de Negocios* (UANL, FIME).
Continúa el análisis de negocio de la Unidad 2 (BRD, user stories, glosario y BPMN) y lo convierte en una
propuesta de arquitectura que separa **dominio, aplicación e infraestructura**.

| | |
|---|---|
| **Empresa** | Sazón Urbano (restaurante con servicio en mesa, para llevar y a domicilio) |
| **Equipo** | 3 |
| **Integrantes** | Emmanuel Carrillo Loera · Edgar Daniel del Ángel Hernández · Fatima Alejandra Cavazos Serrato |
| **Curso / profesor** | Componentes de Lógica de Negocios · Miguel Ángel Gómez Marroquín |
| **Fecha de entrega** | 17/10/2026 |

## Alcance

Se diseñan **5 casos de uso** tomados del BRD de la Unidad 2:

| Caso | Descripción | Reglas principales |
|---|---|---|
| CU-01 | Registrar pedido | RN-01, RN-14 |
| CU-02 | Aplicar promoción | RN-04, RN-05 |
| CU-03 | Cancelar pedido | RN-02, RN-03, RN-10 |
| CU-04 | Gestionar producto agotado | RN-06, RN-12 |
| CU-05 | Asignar repartidor y registrar entrega | RN-11 |

Quedan **fuera** de este diseño (pero contabilizados en la matriz de trazabilidad): inventario en tiempo real,
alertas de existencia mínima, pedidos retrasados y reportes.

## Decisiones principales

- **Patrón de lógica de negocio:** Domain Model como patrón principal; Transaction Script solo para marcar un
  producto agotado; Table Module descartado en los 5 casos (ADR-01).
- **Persistencia:** interfaces de Repository en el dominio, implementaciones en infraestructura y una Unit of Work
  por solicitud (ADR-02).
- **CQRS básico:** Commands y Queries con handlers, DTO de lectura y una sola base de datos (ADR-03).
- **Revisión SOLID:** 7 hallazgos y 3 correcciones aplicadas.

## Cómo revisar este repositorio

| Orden | Qué revisar | Dónde |
|---|---|---|
| 1 | Decisiones de arquitectura (ADR) | `docs/adr/` |
| 2 | Diagrama de clases (fuente PlantUML y PNG) | `diagramas/clases.puml`, `diagramas/clases.png` |
| 3 | Diagramas de secuencia (fuente y PNG) | `diagrams/secuencia-registrar-pedido.*`, `diagramas/secuencia-cancelar-pedido.*` |
| 4 | Diagrama de Dominio (drawio) | `diagramas/Dominio*`|
| 5 | Código base | `src/sazon_urbano/` (`dominio`, `aplicacion`, `infraestructura`) |
| 6 | Pruebas | `tests/` |
| 7 | Bitácora de uso de IA | `docs/Bitácora de IA.pdf` |

## Cómo ejecutar las pruebas

Requisitos: Python 3.10 o superior. No hay dependencias que instalar.

```
python -m unittest discover -v
```

Las pruebas cubren los 5 casos de uso y verifican por código la regla de dependencias
(el dominio no importa aplicación ni infraestructura, ni librerías de SQL).

## Estructura

```
docs/        Informe, ADR, matriz de trazabilidad y bitácora de IA
diagrams/    Archivos fuente (.puml) y exportaciones (.png)
src/         sazon_urbano/dominio · aplicacion · infraestructura
tests/       Pruebas de los casos de uso y de la arquitectura
```

## Supuestos y hallazgos

Los hallazgos sobre la Unidad 2 y los supuestos pendientes de validación (por ejemplo, Mesero y Caja como roles
separados) están registrados en `docs/matriz-trazabilidad.md`.

## Pruebas de la Unidad 5 (pytest, cobertura y CI)

Las pruebas de la Unidad 3 (`unittest`) siguen funcionando y ahora también se ejecutan con **pytest**, que además
corre las nuevas pruebas de la Unidad 5 (`tests/test_pia_unidad5.py`, casos PIA-01 a PIA-21).

```
python -m pip install -r requirements.txt
python -m pytest -v
python -m ruff check src tests
python -m pytest -v --cov --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

| Qué | Dónde |
|---|---|
| Casos de prueba (esperado vs real, tipo y estado) | `docs/matriz_pruebas_pia.csv` |
| Definición de los casos | `tests/matriz_pia.py` |
| Pruebas nuevas de la Unidad 5 | `tests/test_pia_unidad5.py` |
| Reporte HTML de cobertura | `htmlcov/index.html` (se genera con el comando de cobertura) |
| Pipeline de GitHub Actions | `.github/workflows/ci.yml` |

Para regenerar la matriz con los resultados reales: `GENERAR_MATRIZ=1 python -m pytest` (en PowerShell:
`$env:GENERAR_MATRIZ=1; python -m pytest`).
No se modificó el código de `src/`: las pruebas verifican el comportamiento tal como quedó en la Unidad 3.

## Uso de IA

Se usó Claude (Anthropic) como apoyo. Cada propuesta fue revisada contra el BRD y la guía de la actividad.
Los prompts, errores detectados y decisiones del equipo están en `docs/bitacora-ia.md`.
