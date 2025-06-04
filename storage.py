# storage.py

import os, ast
from model import cobro, pago, cliente

def ensure_data_directory():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

# — IDs ——————————————————————————

def get_next_cobro_id():
    path = os.path.join(ensure_data_directory(), 'cobros.txt')
    if not os.path.exists(path):
        return 1
    return len([l for l in open(path,'r',encoding='utf-8') if l.strip()]) + 1

def get_next_pago_id():
    path = os.path.join(ensure_data_directory(), 'pagos.txt')
    if not os.path.exists(path):
        return 1
    return len([l for l in open(path,'r',encoding='utf-8') if l.strip()]) + 1

def get_next_clients_id():
    path = os.path.join(ensure_data_directory(), 'clientes.txt')
    if not os.path.exists(path):
        return 1
    return len([l for l in open(path,'r',encoding='utf-8') if l.strip()]) + 1

# — Guardar cobros ———————————————————

def save_cobros(cobros_tuple):
    """
    Graba la tupla de 20 campos en cobros.txt
    """
    try:
        path = os.path.join(ensure_data_directory(), 'cobros.txt')
        with open(path, 'a', encoding='utf-8') as f:
            for c in cobros_tuple:
                record = (
                    c.id, c.fecha, c.nombreCompleto, c.numParcela,
                    c.imputacion1, c.concepto1, c.importeBruto1,
                    c.imputacion2, c.concepto2, c.importeBruto2,
                    c.imputacion3, c.concepto3, c.importeBruto3,
                    c.numCuentaA, c.montoA, c.numCuentaB, c.montoB,
                    c.impuestoDBCRb, c.anticipoIIBB, c.iva, c.observaciones
                )
                f.write(repr(record) + "\n")
        return True
    except Exception as e:
        print("Error saving cobros:", e)
        return False

# — Guardar pagos ———————————————————

def save_pagos(pagos_tuple):
    """
    Graba la tupla de 9 campos en pagos.txt
    """
    try:
        path = os.path.join(ensure_data_directory(), 'pagos.txt')
        with open(path, 'a', encoding='utf-8') as f:
            for p in pagos_tuple:
                record = (
                    p.id, p.fecha, p.razonSocial, p.concepto, p.tipoComprobante,
                    p.numCuenta, p.montoNeto, p.iva, p.cuentaAcreditar, p.impuestoDBCRb
                )
                f.write(repr(record) + "\n")
        return True
    except Exception as e:
        print("Error saving pagos:", e)
        return False

# — Guardar clientes ——————————————————

def save_clients(clients_tuple):
    """
    Graba la tupla de 13 campos en clientes.txt
    """
    try:
        path = os.path.join(ensure_data_directory(), 'clientes.txt')
        with open(path, 'a', encoding='utf-8') as f:
            for c in clients_tuple:
                record = (
                    c.id, c.nombreCompleto, c.DNI, c.direccion,
                    c.telefono1, c.telefono2, c.email,
                    c.parcela1, c.parcela2, c.parcela3,
                    c.superficie, c.observaciones
                )
                f.write(repr(record) + "\n")
        return True
    except Exception as e:
        print("Error saving clientes:", e)
        return False

# — Plan de Cuentas ——————————————————

PLAN_FILE = 'plan_cuentas.txt'
def load_plan_cuentas():
    path = os.path.join(ensure_data_directory(), PLAN_FILE)
    if not os.path.exists(path):
        return []
    return [ast.literal_eval(l) for l in open(path,'r',encoding='utf-8') if l.strip()]

def save_plan_cuentas(plan_tuple):
    path = os.path.join(ensure_data_directory(), PLAN_FILE)
    with open(path, 'a', encoding='utf-8') as f:
        for pc in plan_tuple:
            f.write(repr(pc) + "\n")
    return True

TAX_COBROS_FILE = 'tax_cobros.txt'
def load_tax_cobros():
    path = os.path.join(ensure_data_directory(), TAX_COBROS_FILE)
    tbl = {}
    if os.path.exists(path):
        for l in open(path, 'r', encoding='utf-8'):
            if not l.strip(): continue
            num, pct_iibb, pct_dbcr = ast.literal_eval(l)
            tbl[str(num)] = (float(pct_iibb), float(pct_dbcr))
    return tbl

def save_tax_cobros(tax_tuple):
    path = os.path.join(ensure_data_directory(), TAX_COBROS_FILE)
    with open(path, 'a', encoding='utf-8') as f:
        for num, pct_iibb, pct_dbcr in tax_tuple:
            f.write(repr((num, pct_iibb, pct_dbcr)) + "\n")
    return True

# Para Pagos (solo DByCR bancario)
TAX_PAGOS_FILE = 'tax_pagos.txt'
def load_tax_pagos():
    path = os.path.join(ensure_data_directory(), TAX_PAGOS_FILE)
    tbl = {}
    if os.path.exists(path):
        for l in open(path, 'r', encoding='utf-8'):
            if not l.strip(): continue
            num, pct_dbcr = ast.literal_eval(l)
            tbl[str(num)] = float(pct_dbcr)
    return tbl

def save_tax_pagos(tax_tuple):
    path = os.path.join(ensure_data_directory(), TAX_PAGOS_FILE)
    with open(path, 'a', encoding='utf-8') as f:
        for num, pct_dbcr in tax_tuple:
            f.write(repr((num, pct_dbcr)) + "\n")
    return True
