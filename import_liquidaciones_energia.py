#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importa datos de LIQUIDACIONES ENERGIA.ods a data/liquidaciones_energia.txt.
Si pandas no está disponible, usa un parser ODS simple.
Solo se consideran las primeras 342 filas y se descartan columnas vacías."""

import os
import zipfile
import xml.etree.ElementTree as ET

try:
    import pandas as pd  # type: ignore
except Exception:  # pandas no disponible
    pd = None


def ensure_data_directory():
    """Asegura que exista la carpeta data/ y devuelve su ruta."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _leer_ods_sin_pandas(path):
    """Lee un archivo ODS y devuelve una lista de filas (tuplas de celdas)."""
    rows = []
    with zipfile.ZipFile(path) as zf:
        with zf.open("content.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()
    ns = {
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }
    for row in root.findall(".//table:table-row", ns):
        cells = []
        for cell in row.findall("table:table-cell", ns):
            repeat = int(cell.attrib.get(f"{{{ns['table']}}}number-columns-repeated", "1"))
            text = "".join(p.text or "" for p in cell.findall("text:p", ns))
            for _ in range(repeat):
                cells.append(text)
        if any(cells):
            rows.append(tuple(cells))
    return rows


def _descartar_columnas_vacias(filas):
    """Devuelve las filas solo con las columnas que tienen contenido."""
    if not filas:
        return filas
    max_cols = max(len(f) for f in filas)
    filas = [f + ("",) * (max_cols - len(f)) for f in filas]
    keep = [i for i in range(max_cols) if any(row[i].strip() for row in filas)]
    return [tuple(row[i] for i in keep) for row in filas]


def importar_liquidaciones_desde_ods(ruta_ods):
    """Lee la planilla ODS y guarda cada fila como tupla en un TXT."""
    data_dir = ensure_data_directory()
    path_txt = os.path.join(data_dir, "liquidaciones_energia.txt")

    if pd is not None:
        df = pd.read_excel(ruta_ods, engine="odf")
        df = df.iloc[:342]  # limitar filas
        # descartar columnas totalmente vacías
        df = df.dropna(axis=1, how="all")
        filas = [
            tuple(
                "" if val is None or (isinstance(val, float) and pd.isna(val)) else str(val).strip()
                for val in row
            )
            for row in df.itertuples(index=False, name=None)
        ]
        filas = _descartar_columnas_vacias(filas)
    else:
        filas = _leer_ods_sin_pandas(ruta_ods)
        filas = filas[:342]
        filas = _descartar_columnas_vacias(filas)

    with open(path_txt, "w", encoding="utf-8") as f_txt:
        importados = 0
        for fila in filas:
            if not any(fila):
                continue
            f_txt.write(repr(fila) + "\n")
            importados += 1

    print(f"Se importaron {importados} registros en:\n  {path_txt}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        ruta_ods = sys.argv[1]
    else:
        ruta_ods = os.path.join(os.path.dirname(__file__), "LIQUIDACIONES ENERGIA.ods")

    if not os.path.exists(ruta_ods):
        print(
            "No se encontró el archivo ODS:\n"
            f"  {ruta_ods}\n"
            "Indique la ruta como argumento al ejecutar el script."
        )
        sys.exit(1)

    importar_liquidaciones_desde_ods(ruta_ods)
