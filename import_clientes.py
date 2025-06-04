#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv

def ensure_data_directory():
    """Se asegura de que exista la carpeta data/ y la devuelve."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_next_clients_id(path_clientes_txt):
    """
    Devuelve el próximo ID para clientes.txt.
    Si no existe el archivo, retorna 1; 
    si existe, cuenta cuántas líneas no vacías hay y suma 1.
    """
    if not os.path.exists(path_clientes_txt):
        return 1
    with open(path_clientes_txt, 'r', encoding='utf-8') as f:
        líneas = [línea for línea in f if línea.strip()]
    return len(líneas) + 1

def importar_clientes_desde_csv(ruta_csv):
    data_dir = ensure_data_directory()
    path_clientes_txt = os.path.join(data_dir, 'clientes.txt')

    importados = 0
    with open(ruta_csv, 'r', encoding='latin-1', newline='') as f:
        lector = csv.reader(f, delimiter=',')
        # Saltar la primera línea (solo comas)
        try:
            next(lector)
        except StopIteration:
            return

        # Leer encabezados (segunda línea)
        try:
            headers = next(lector)
        except StopIteration:
            return

        # Definimos índices según orden de columnas en el CSV:
        # 0: Num Cliente
        # 1: Apellido y Nombre
        # 2: DNI
        # 3: DIRECCIÓN (aparece como 'DIRECCIï¿½N' en Latin-1)
        # 4: Teléfono 1  (aparece como 'Telï¿fono 1 ')
        # 5: Teléfono 2  (aparece como 'Telïfono 2 ')
        # 6: email
        # 7: Parcela1
        # 8:  parcela2  (con espacio inicial)
        # 9: parcela3
        # 10: Superficie (m�)
        # 11: Observaciones

        for fila in lector:
            if not fila or not fila[0].strip():
                continue

            full_name  = fila[1].strip()
            dni        = fila[2].strip()
            direccion  = fila[3].strip()
            tel1       = fila[4].strip()
            tel2       = fila[5].strip()
            email      = fila[6].strip()
            p1         = fila[7].strip()
            p2         = fila[8].strip()
            p3         = fila[9].strip()
            superficie = fila[10].strip()
            obs        = fila[11].strip()

            nuevo_id = get_next_clients_id(path_clientes_txt)

            tupla_cliente = (
                nuevo_id,
                full_name,
                dni,
                direccion,
                tel1,
                tel2,
                email,
                p1,
                p2,
                p3,
                superficie,
                obs
            )

            with open(path_clientes_txt, 'a', encoding='utf-8') as f_txt:
                f_txt.write(repr(tupla_cliente) + "\n")

            importados += 1

    print(f"Se importaron {importados} clientes en:\n  {path_clientes_txt}")

if __name__ == "__main__":
    ruta_csv = os.path.join(os.path.dirname(__file__), "base_para_archivo_de_clientes[1].csv")
    importar_clientes_desde_csv(ruta_csv)
