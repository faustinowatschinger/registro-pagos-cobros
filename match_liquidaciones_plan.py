import os
import ast
import re
import difflib
import unicodedata

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LIQ_FILE = os.path.join(DATA_DIR, 'liquidaciones_energia.txt')
if not os.path.exists(LIQ_FILE):
    LIQ_FILE = os.path.join(DATA_DIR, 'liquidacion.txt')
PLAN_FILE = os.path.join(DATA_DIR, 'plan_cuentas.txt')

def _norm(text):
    text = unicodedata.normalize('NFD', str(text))
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    return text.upper()

def load_liq_names():
    names = set()
    if not os.path.exists(LIQ_FILE):
        return []
    with open(LIQ_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                tup = ast.literal_eval(line)
            except Exception:
                continue
            if not isinstance(tup, tuple) or not tup:
                continue
            if 'CLIENTE' in str(tup[0]).upper():
                continue
            name = str(tup[0]).strip()
            if not name:
                continue
            names.add(name)
    return sorted(names)

def load_plan_map():
    plan = []
    if not os.path.exists(PLAN_FILE):
        return plan
    with open(PLAN_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                code, name = ast.literal_eval(line)
            except Exception:
                continue
            if str(code).startswith('11-26-'):
                clean = name.split('-', 1)[-1].strip()
                norm = _norm(clean)
                plan.append((code, norm, set(norm.split())))
    return plan

def find_code(nombre, plan_map):
    tokens = set(_norm(nombre).split())
    for code, norm, tokens_plan in plan_map:
        ok = True
        for tok in tokens:
            if not any(difflib.SequenceMatcher(None, tok, tp).ratio() > 0.8 for tp in tokens_plan):
                ok = False
                break
        if ok:
            return code
    return None

def main():
    names = load_liq_names()
    plan_map = load_plan_map()
    for n in names:
        code = find_code(n, plan_map)
        print(f"{code or 'N/A'}\t{n}")

if __name__ == '__main__':
    main()
