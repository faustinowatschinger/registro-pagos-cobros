#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Herramienta para importar plan de cuentas de liquidación.

Este script lee un archivo CSV y agrega sus filas al archivo
``data/plan_cuentas.txt``. Solo se procesan las primeras 342 filas
útiles (sin contar encabezados). Cada fila debe contener al menos dos
columnas: número de cuenta y denominación.
"""

import csv
import os

MAX_FILAS = 342


def ensure_data_directory():
    """Se asegura de que exista la carpeta data/ y la devuelve."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def importar_liquidacion_desde_csv(ruta_csv):
    data_dir = ensure_data_directory()
    path_plan = os.path.join(data_dir, "plan_cuentas.txt")

    importados = 0
    with open(ruta_csv, "r", encoding="latin-1", newline="") as f:
        lector = csv.reader(f)
        try:
            next(lector)  # Encabezados
        except StopIteration:
            return

        for idx, fila in enumerate(lector, start=1):
            if idx > MAX_FILAS:
                break
            if not fila or not fila[0].strip():
                continue
            cuenta = fila[0].strip()
            nombre = fila[1].strip() if len(fila) > 1 else ""
            with open(path_plan, "a", encoding="utf-8") as f_txt:
                f_txt.write(repr((cuenta, nombre)) + "\n")
            importados += 1

    print(f"Se importaron {importados} cuentas en:\n  {path_plan}")


if __name__ == "__main__":
    ruta = os.path.join(os.path.dirname(__file__), "liquidacion.csv")
    importar_liquidacion_desde_csv(ruta)
