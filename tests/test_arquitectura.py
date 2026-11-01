"""Pruebas de arquitectura: verifican por código la regla de dependencias (principio D de SOLID,
validación de Persistencia de la Etapa 9)."""
import ast
import pathlib
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1] / "src" / "sazon_urbano"


def importaciones(carpeta: str) -> set:
    encontradas = set()
    for archivo in (RAIZ / carpeta).glob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                encontradas.add(nodo.module)
            elif isinstance(nodo, ast.Import):
                encontradas.update(a.name for a in nodo.names)
    return encontradas


class TestReglaDeDependencias(unittest.TestCase):
    def test_el_dominio_no_depende_de_aplicacion_ni_infraestructura(self):
        for modulo in importaciones("dominio"):
            self.assertNotIn("aplicacion", modulo)
            self.assertNotIn("infraestructura", modulo)

    def test_la_aplicacion_no_depende_de_la_infraestructura(self):
        for modulo in importaciones("aplicacion"):
            self.assertNotIn("infraestructura", modulo)

    def test_el_dominio_no_usa_sql_ni_librerias_de_persistencia(self):
        prohibidas = {"sqlite3", "sqlalchemy", "psycopg2", "pyodbc"}
        self.assertFalse(prohibidas & importaciones("dominio"))


if __name__ == "__main__":
    unittest.main()
