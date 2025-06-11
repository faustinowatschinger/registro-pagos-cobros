# storage.py

import os, ast, datetime
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
    Graba la tupla de 24 campos en cobros.txt
    """
    try:
        path = os.path.join(ensure_data_directory(), 'cobros.txt')
        with open(path, 'a', encoding='utf-8') as f:
            for c in cobros_tuple:
                record = (
                    c.id, c.fecha, c.nombreCompleto, c.numParcela,
                    c.imputacion1, c.concepto1, c.fecha1, c.importeBruto1,
                    c.imputacion2, c.concepto2, c.fecha2, c.importeBruto2,
                    c.imputacion3, c.concepto3, c.fecha3, c.importeBruto3,
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
    """Return dict {cuenta: (iibb_decimal, dbcr_decimal)}"""
    path = os.path.join(ensure_data_directory(), TAX_COBROS_FILE)
    tbl = {}
    if os.path.exists(path):
        for l in open(path, 'r', encoding='utf-8'):
            if not l.strip():
                continue
            num, pct_iibb, pct_dbcr = ast.literal_eval(l)
            # values are stored as percentages, convert to decimals
            tbl[str(num)] = (
                float(pct_iibb) / 100.0,
                float(pct_dbcr) / 100.0,
            )
    return tbl


def save_tax_cobros(tax_tuple):
    """Save decimals as percentages for persistence"""
    path = os.path.join(ensure_data_directory(), TAX_COBROS_FILE)
    with open(path, 'a', encoding='utf-8') as f:
        for num, pct_iibb, pct_dbcr in tax_tuple:
            f.write(
                repr(
                    (
                        num,
                        float(pct_iibb) * 100.0,
                        float(pct_dbcr) * 100.0,
                    )
                )
                + "\n"
            )
    return True

# Para Pagos (solo DByCR bancario)
TAX_PAGOS_FILE = 'tax_pagos.txt'

def load_tax_pagos():
    """Return dict {cuenta: dbcr_decimal}"""
    path = os.path.join(ensure_data_directory(), TAX_PAGOS_FILE)
    tbl = {}
    if os.path.exists(path):
        for l in open(path, 'r', encoding='utf-8'):
            if not l.strip():
                continue
            num, pct_dbcr = ast.literal_eval(l)
            tbl[str(num)] = float(pct_dbcr) / 100.0
    return tbl


def save_tax_pagos(tax_tuple):
    """Persist decimals as percentages"""
    path = os.path.join(ensure_data_directory(), TAX_PAGOS_FILE)
    with open(path, 'a', encoding='utf-8') as f:
        for num, pct_dbcr in tax_tuple:
            f.write(repr((num, float(pct_dbcr) * 100.0)) + "\n")
    return True

# --- Expensas -------------------------------------------------

EXPENSAS_FILE = 'expensas.txt'

def load_expensas():
    """Return list of tuples [(cuenta, fecha, monto), ...]"""
    path = os.path.join(ensure_data_directory(), EXPENSAS_FILE)
    data = []
    if os.path.exists(path):
        for line in open(path, 'r', encoding='utf-8'):
            if not line.strip():
                continue
            try:
                cuenta, fecha, monto = ast.literal_eval(line)
            except Exception:
                # Formato previo: dict {cuenta: [mes, saldo]}
                try:
                    cuenta, mes, saldo = ast.literal_eval(line)
                    data.append((str(cuenta), str(mes), float(saldo)))
                    continue
                except Exception:
                    continue
            data.append((str(cuenta), str(fecha), float(monto)))
    return data

def save_expensas(exp_list):
    path = os.path.join(ensure_data_directory(), EXPENSAS_FILE)
    with open(path, 'w', encoding='utf-8') as f:
        for rec in exp_list:
            cuenta, fecha, monto = rec
            f.write(repr((cuenta, fecha, monto)) + "\n")
    return True

def update_expensas(plan_dict):
    """Add a new positive entry each month for every expensa account."""
    exps = load_expensas()
    cur_month = datetime.date.today().strftime('%Y-%m')
    updated = False
    # Determine last month recorded for each account
    last_months = {}
    for c, fecha, monto in exps:
        if not str(c).startswith('11-21-'):
            continue
        mes = fecha[:7]
        last_months[c] = max(mes, last_months.get(c, '0000-00'))

    for acc in plan_dict:
        if not str(acc).startswith('11-21-'):
            continue
        last = last_months.get(acc)
        if last != cur_month:
            exps.append((str(acc), cur_month, 33900.0))
            updated = True
    if updated:
        save_expensas(exps)

def apply_payment_expensa(cuenta, amount, fecha):
    """Append a negative payment record for the given account.

    The date is stored as ``YYYY-MM`` to match monthly expensa entries.
    """

    def _month_from(f):
        if isinstance(f, (datetime.date, datetime.datetime)):
            return f.strftime('%Y-%m')
        s = str(f)
        try:
            dt = datetime.datetime.strptime(s, '%d/%m/%Y')
            return dt.strftime('%Y-%m')
        except Exception:
            pass
        try:
            dt = datetime.datetime.strptime(s[:10], '%Y-%m-%d')
            return dt.strftime('%Y-%m')
        except Exception:
            pass
        return s[:7]

    exps = load_expensas()
    mes = _month_from(fecha)
    exps.append((str(cuenta), mes, -abs(float(amount))))
    save_expensas(exps)
