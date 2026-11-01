"""Si se ejecuta con GENERAR_MATRIZ=1, escribe docs/matriz_pruebas_pia.csv al terminar la sesión."""
import csv
import os
from pathlib import Path

import pytest

from .matriz_pia import CASOS, OBSERVADO

_RESULTADOS: dict = {}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    informe = resultado.get_result()
    if informe.when == "call":
        _RESULTADOS[item.name.split("[")[0]] = "PASSED" if informe.passed else "FAILED"


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("GENERAR_MATRIZ") != "1":
        return
    destino = Path(session.config.rootpath) / "docs" / "matriz_pruebas_pia.csv"
    destino.parent.mkdir(exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["id", "regla", "tipo", "entrada", "resultado_esperado", "resultado_real", "estado", "prueba"])
        for caso_id, regla, tipo, entrada, esperado, prueba in CASOS:
            escritor.writerow([caso_id, regla, tipo, entrada, esperado, OBSERVADO.get(caso_id, "no ejecutado"),
                               _RESULTADOS.get(prueba, "NO EJECUTADO"), prueba])
