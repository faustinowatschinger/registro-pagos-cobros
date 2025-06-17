#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importa datos de LIQUIDACIONES ENERGIA.ods a data/liquidaciones_energia.txt."""

import os
import pandas as pd


def ensure_data_directory():
    """Asegura que exista la carpeta data/ y devuelve su ruta."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def importar_liquidaciones_desde_ods(ruta_ods):
    """Lee la planilla ODS y guarda cada fila como tupla en un TXT."""
    data_dir = ensure_data_directory()
    path_txt = os.path.join(data_dir, 'liquidaciones_energia.txt')

    df = pd.read_excel(ruta_ods, engine='odf', dtype=str)

    importados = 0
    with open(path_txt, 'w', encoding='utf-8') as f_txt:
        for row in df.itertuples(index=False, name=None):
            fila = tuple('' if val is None or (isinstance(val, float) and pd.isna(val)) else str(val).strip() for val in row)
            if not any(fila):
                continue
            f_txt.write(repr(fila) + '\n')
            importados += 1

    print(f"Se importaron {importados} registros en:\n  {path_txt}")


if __name__ == '__main__':
    ruta_ods = os.path.join(os.path.dirname(__file__), 'LIQUIDACIONES ENERGIA.ods')
    importar_liquidaciones_desde_ods(ruta_ods)
