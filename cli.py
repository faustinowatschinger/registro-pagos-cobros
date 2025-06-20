import os
import ast
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from model import cobro, pago, cliente
from storage import (
    save_cobros, save_pagos, save_clients,
    load_plan_cuentas, load_tax_cobros, save_tax_cobros,
    load_tax_pagos, save_tax_pagos,
    save_plan_cuentas,
    get_next_cobro_id, get_next_pago_id, get_next_clients_id,
    ensure_data_directory
)

BRANCH_CODE = "0001"

# Estilos globales
def build_styles(root):
    style = ttk.Style(root)
    style.configure('Nav.TButton',   font=('Segoe UI', 12), padding=8, width=20)
    style.configure('Big.TButton',   font=('Segoe UI', 14), padding=6)
    style.configure('Field.TLabel',  font=('Segoe UI', 12))
    style.configure('Field.TEntry',  font=('Segoe UI', 12))
    style.configure('Title.TLabel',  font=('Segoe UI', 16, 'bold'))
    style.configure('Header.TLabel', font=('Segoe UI', 14))
    return style

class PlaceholderEntry(ttk.Entry):
    """Entry widget with placeholder text support."""

    def __init__(self, master=None, placeholder="", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self._ph_visible = False
        self.bind("<FocusIn>", self._clear)
        self.bind("<FocusOut>", self._show)
        self._show()

    def _show(self, event=None):
        if not self.get():
            self._ph_visible = True
            self.insert(0, self.placeholder)
            self.configure(foreground="gray")

    def _clear(self, event=None):
        if self._ph_visible:
            self.delete(0, "end")
            self.configure(foreground="black")
            self._ph_visible = False

# Lectura genérica de registros
def read_records(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [ast.literal_eval(line) for line in f if line.strip()]

def overwrite_records(path, lista_registros):
    """
    Reescribe completamente el archivo `path` con la lista de tuplas `lista_registros`.
    Cada elemento de lista_registros debe ser una tupla (o lista) que represente
    exactamente el record a guardar (igual que hace save_cobros o save_pagos).
    """
    with open(path, 'w', encoding='utf-8') as f:
        for r in lista_registros:
            f.write(repr(r) + "\n")


def filter_rows(lista_registros, filtros):
    """
    Dada la lista completa de registros (lista de tuplas) y un diccionario `filtros`
    donde la clave es el índice de columna (0, 1, 2, ...) y el valor es la cadena
    de filtro (se busca substring, case-insensitive),
    retorna solo aquellas filas que coincidan en todas las columnas filtradas.
    """
    resultado = []
    for row in lista_registros:
        match = True
        for col_idx, texto in filtros.items():
            if texto.strip() == "":
                continue
            celda = str(row[col_idx])
            if texto.lower() not in celda.lower():
                match = False
                break
        if match:
            resultado.append(row)
    return resultado


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Sistema de Cobros y Pagos')
        self.state('zoomed')
        build_styles(self)

        # Cargo datos iniciales
        self._load_data()

        # 1) Construyo la UI de navegación y el contenedor "self.content"
        self._build_ui()

        # 2) Creo todos los frames vacíos DENTRO de self.content, pero sin packearlos
        self.frames = {}
        for name in [
            'cobro', 'pago', 'cliente',
            'lst_cobros', 'lst_pagos', 'lst_clientes',
            'plan', 'tax_cobros', 'tax_pagos'
        ]:
            self.frames[name] = ttk.Frame(self.content)

        # 3) Relleno (pueblo) cada frame con su contenido, SIN empaquetarlo aquí
        self._build_cobro(self.frames['cobro'])
        self._build_pago(self.frames['pago'])
        self._build_cliente(self.frames['cliente'])
        self._build_list(self.frames['lst_cobros'],   'cobros.txt')
        self._build_list(self.frames['lst_pagos'],    'pagos.txt')
        self._build_list(self.frames['lst_clientes'], 'clientes.txt')
        self._build_plan(self.frames['plan'])
        self._build_tax_cobros(self.frames['tax_cobros'])
        self._build_tax_pagos(self.frames['tax_pagos'])

        # 4) Al arrancar, muestro sólo la vista "cobro"
        self._show_frame('cobro')


    def _load_data(self):
        data_dir = ensure_data_directory()
        self.clientes = {
            str(r[0]): r
            for r in read_records(os.path.join(data_dir, 'clientes.txt'))
        }
        self.plan = {
            str(pc[0]): pc[1]
            for pc in load_plan_cuentas()
        }


    def _build_ui(self):
        # Contenedor lateral de navegación
        self.nav = ttk.Frame(self, width=200, relief='raised')
        self.nav.pack(side='left', fill='y')

           # Contenedor principal donde irán los distintos "frames"
        self.content = ttk.Frame(self)
        self.content.pack(side='right', expand=True, fill='both')

        # Botones de navegación
        pages = [
            ('Cobro', 'cobro'), ('Pago', 'pago'), ('Cliente', 'cliente'),
            ('Ver Cobros', 'lst_cobros'), ('Ver Pagos', 'lst_pagos'), ('Ver Clientes', 'lst_clientes'),
            ('Plan Ctas', 'plan'),
            ('Imp. Cobros', 'tax_cobros'),
            ('Imp. Pagos',  'tax_pagos'),
        ]
        for txt, name in pages:
            ttk.Button(
                self.nav,
                text=txt,
                style='Nav.TButton',
                command=lambda n=name: self._show_frame(n)
            ).pack(pady=5)


    def _show_frame(self, name):
        # 1) Oculto (forget) todos los frames
        for f in self.frames.values():
            f.pack_forget()

        # 2) Para las vistas de lista y tablas dinámicas, reconstruyo SU contenido
        #    (porque pueden haber cambiado los datos en disco).
        if name == 'lst_cobros':
            self._build_list(self.frames[name], 'cobros.txt')
        elif name == 'lst_pagos':
            self._build_list(self.frames[name], 'pagos.txt')
        elif name == 'lst_clientes':
            self._build_list(self.frames[name], 'clientes.txt')
        elif name == 'tax_cobros':
            self._build_tax_cobros(self.frames[name])
        elif name == 'tax_pagos':
            self._build_tax_pagos(self.frames[name])
        elif name == 'plan':                      
            self._build_plan(self.frames[name])

        # 3) Finalmente, empaco (pack) solo el frame que quiero mostrar
        self.frames[name].pack(expand=True, fill='both')


    # ---------------------------
    #  Métodos que “pueblan” cada frame
    #  (todos ellos CREAN widgets DENTRO de ‘parent’, PERO NO HACEN parent.pack())
    # ---------------------------

    def _build_list(self, parent, filename):
        # 0) Limpiar todo el contenido de 'parent'
        for w in parent.winfo_children():
            w.destroy()

        # 1) Título
        pretty_name = filename.split('.')[0].capitalize()
        ttk.Label(parent, text=f'Listado de {pretty_name}', style='Title.TLabel')\
            .pack(pady=10)

        # 2) Contenedor principal
        cont = ttk.Frame(parent, padding=10)
        cont.pack(expand=True, fill='both')

        # 3) Leer registros desde disco
        full_path = os.path.join(ensure_data_directory(), filename)
        registros = read_records(full_path)
        if not registros:
            ttk.Label(cont, text='No hay registros.', style='Field.TLabel')\
                .pack(pady=20)
            return

        # 4) Determinar encabezados
        headers_map = {
            'cobros.txt': [
                'ID','Fecha','Nombre y Apellido','Parcela',
                'Imp1 Cod','Imp1 Desc','Imp1 Importe',
                'Imp2 Cod','Imp2 Desc','Imp2 Importe',
                'Imp3 Cod','Imp3 Desc','Imp3 Importe',
                'Cuenta A','Monto A','Cuenta B','Monto B',
                'DByCR %','IIBB %','IVA %','Observaciones'
            ],
            'pagos.txt': [
                'ID','Fecha','Razón Social','Concepto',
                'Tipo Comp.','Cuenta Imp.','Importe Neto',
                'Importe c/IVA','Cuenta Paga','DByCR Banc.'
            ],
            'clientes.txt': [
                'ID','Nombre y Apellido','DNI','Dirección',
                'Teléfono 1','Teléfono 2','Email',
                'Parcela 1','Parcela 2','Parcela 3',
                'Superficie','Observaciones'
            ]
        }
        headers = headers_map.get(filename, [f'C{i+1}' for i in range(len(registros[0]))])

        # 5) Creamos un sub-frame para la tabla y otro Canvas para la fila de
        #    filtros para que se desplace junto con el Treeview.
        table = ttk.Frame(cont)
        table.grid(row=0, column=0, sticky='nsew')
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)

        filtro_canvas = tk.Canvas(table, highlightthickness=0)
        filtro_canvas.grid(row=0, column=0, columnspan=len(headers), sticky='ew')
        filtro_canvas.configure(xscrollcommand=lambda *a: hsb.set(*a))

        filtro_frame = ttk.Frame(filtro_canvas)
        filtro_canvas.create_window((0, 0), window=filtro_frame, anchor='nw')
        filtro_entrys = {}
        for col_index, col_name in enumerate(headers):
            ent = PlaceholderEntry(filtro_frame, placeholder=col_name, style='Field.TEntry')
            ent.grid(row=0, column=col_index, padx=1, sticky='ew')
            filtro_frame.grid_columnconfigure(col_index, weight=1)
            filtro_entrys[col_index] = ent

        # 6) Ahora creamos el Treeview justo debajo de la fila de filtros.
        #    El Treeview ocupará tantas columnas como 'headers',
        #    y la scrollbar vertical irá en la columna 'len(headers)'.
        filtro_canvas.update_idletasks()
        filtro_canvas.configure(scrollregion=filtro_canvas.bbox('all'))

        vsb = ttk.Scrollbar(table, orient='vertical')
        hsb = ttk.Scrollbar(table, orient='horizontal')

        def _tree_xview(*args):
            filtro_canvas.xview_moveto(args[0])
            hsb.set(*args)

        tree = ttk.Treeview(
            table,
            columns=headers,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=_tree_xview
        )
        vsb.config(command=tree.yview)

        def _scroll_x(*args):
            tree.xview(*args)
            filtro_canvas.xview(*args)

        hsb.config(command=_scroll_x)

        # Ubicamos el Treeview en row=1, column=0..(len(headers)-1)
        tree.grid(row=1, column=0, columnspan=len(headers), sticky='nsew')
        # Scroll vertical a la derecha del Treeview
        vsb.grid(row=1, column=len(headers), sticky='ns')
        # Scroll horizontal justo debajo del Treeview
        hsb.grid(row=2, column=0, columnspan=len(headers), sticky='ew')

        table.grid_rowconfigure(1, weight=1)

        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=120, anchor='center')

        # 7) Función para poblar el Treeview
        def poblar_treeview(lista_para_mostrar):
            # Limpiar todo
            for item in tree.get_children():
                tree.delete(item)
            # Insertar filas
            for row in lista_para_mostrar:
                tree.insert('', 'end', values=row)

        # Llenamos inicialmente con todos los registros
        poblar_treeview(registros)

        # 8) Función de filtrado
        def aplicar_filtros(event=None):
            filtros = {idx: ent.get() for idx, ent in filtro_entrys.items()}
            filtrados = filter_rows(registros, filtros)
            poblar_treeview(filtrados)

        # Enlazamos cada Entry de filtro para que, al soltar tecla, se aplique el filtro
        for ent in filtro_entrys.values():
            ent.bind('<KeyRelease>', aplicar_filtros)

        # 9) Botón “Eliminar seleccionado”
        btn_frame = ttk.Frame(cont)
        btn_frame.grid(row=1, column=0, sticky='w', pady=(5,0))
        boton_eliminar = ttk.Button(btn_frame, text='Eliminar seleccionado', style='Big.TButton')
        boton_eliminar.grid(row=0, column=0, padx=5)
        boton_editar = ttk.Button(btn_frame, text='Editar seleccionado', style='Big.TButton')
        boton_editar.grid(row=0, column=1, padx=5)

        def eliminar_seleccionado():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Ningún registro seleccionado.')
                return
            valores = tree.item(sel[0], 'values')
            id_seleccion = valores[0]  # asumimos que la primera columna es el ID
            if not messagebox.askyesno('Confirmar', f'¿Eliminar registro con ID = {id_seleccion}?'):
                return

            # Releer archivo y filtrar por ID
            todos = read_records(full_path)
            nuevos = [r for r in todos if str(r[0]) != str(id_seleccion)]
            overwrite_records(full_path, nuevos)

            nonlocal registros
            registros = nuevos
            aplicar_filtros()

        boton_eliminar.config(command=eliminar_seleccionado)

        def editar_seleccionado():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Ningún registro seleccionado.')
                return
            valores = tree.item(sel[0], 'values')
            id_sel = valores[0]
            idx_reg = None
            for i, r in enumerate(registros):
                if str(r[0]) == str(id_sel):
                    idx_reg = i
                    break
            if idx_reg is None:
                return

            orig_row = list(registros[idx_reg])

            win = tk.Toplevel(self)
            win.title('Editar registro')
            entries = []
            for j, h in enumerate(headers):
                ttk.Label(win, text=h, style='Field.TLabel').grid(row=j, column=0, sticky='e', padx=5, pady=2)
                e = ttk.Entry(win, style='Field.TEntry')
                e.grid(row=j, column=1, sticky='w', padx=5, pady=2)
                e.insert(0, str(valores[j]))
                entries.append(e)

            def guardar():
                nuevos = []
                for val, orig in zip(entries, orig_row):
                    txt = val.get()
                    try:
                        if isinstance(orig, int):
                            nuevos.append(int(txt))
                        elif isinstance(orig, float):
                            nuevos.append(float(txt))
                        else:
                            nuevos.append(txt)
                    except ValueError:
                        nuevos.append(txt)
                registros[idx_reg] = tuple(nuevos)
                overwrite_records(full_path, registros)
                aplicar_filtros()
                win.destroy()

            ttk.Button(win, text='Guardar', command=guardar, style='Big.TButton').grid(row=len(headers), column=0, columnspan=2, pady=10)

        boton_editar.config(command=editar_seleccionado)



    def _build_cobro(self, parent):
        # 0) Limpiar cualquier widget previo en “parent”
        for w in parent.winfo_children():
            w.destroy()
    
        # 1) Contenedor principal dentro de “parent”
        cont = ttk.Frame(parent, padding=20, relief='groove')
        cont.place(relx=0.5, rely=0.5, anchor='center')
    
        # 2) Título
        ttk.Label(cont, text='Registro Ingreso', style='Title.TLabel').pack(pady=(0,20))
    
        # — 1) Encabezado —
        header = ttk.Frame(cont, padding=(0,10))
        header.pack(fill='x')
        left = ttk.Frame(header); left.pack(side='left', padx=5)
        ttk.Label(left, text='BIOCULTIVOS SAS',     style='Title.TLabel').pack(anchor='w')
        ttk.Label(left, text='CUIT 30-71841359-8', style='Header.TLabel').pack(anchor='w')
        right = ttk.Frame(header); right.pack(side='right', padx=5)
        ttk.Label(right, text='Condominio El Michay',         style='Header.TLabel').pack(anchor='e')
        ttk.Label(right, text='Chacra 032-E-007-01C',          style='Header.TLabel').pack(anchor='e')
        ttk.Label(right, text='General Fernández Oro (R.N.)', style='Header.TLabel').pack(anchor='e')
    
        # — 2) Fecha / Recibo —
        # (Este bloque dentro de _build_cobro)
        
        # Creamos el Entry y, al final, un label con el número de recibo
        sec1 = ttk.Frame(cont, padding=5)
        sec1.pack(fill='x', pady=(0,10))
        sec1.grid_columnconfigure(0, weight=1)
        sec1.grid_columnconfigure(1, weight=1)
        
        # --- Fecha ---
        fecha_frame = ttk.Frame(sec1)
        fecha_frame.grid(row=0, column=0, sticky='ew')
        ttk.Label(fecha_frame, text='Fecha:', style='Field.TLabel').pack(side='left', padx=5)
        entry_fecha = ttk.Entry(fecha_frame, style='Field.TEntry', width=15)
        entry_fecha.pack(side='left')
        
        # Función auxiliar para construir "DD/MM/YYYY" a partir de una cadena de dígitos
        def formatear_ddmmyyyy(s):
            # s = sólo dígitos (hasta 8) → DDMMYYYY
            if len(s) > 8:
                s = s[:8]
            if len(s) < 3:
                return s
            if len(s) < 5:
                # entre 3 y 4 dígitos → "DD/M" o "DD/MM"
                return s[:2] + "/" + s[2:]
            # 5 o más dígitos → "DD/MM/YYYY"
            return s[:2] + "/" + s[2:4] + "/" + s[4:]
        
        # Inicializar con fecha de hoy
        hoy = datetime.date.today()
        raw_inicial = hoy.strftime("%d%m%Y")  # "DDMMYYYY"
        texto_inicial = formatear_ddmmyyyy(raw_inicial)
        entry_fecha.insert(0, texto_inicial)
        
        # Al soltar cada tecla, reconstruitmos la máscara y reubicamos el cursor
        def on_keyrelease_fecha(event):
            antiguo = entry_fecha.get()
            pos_orig = entry_fecha.index("insert")
        
            # 1) Contamos cuántos dígitos había antes del cursor
            dig_antes = 0
            for ch in antiguo[:pos_orig]:
                if ch.isdigit():
                    dig_antes += 1
        
            # 2) Extraemos sólo los dígitos (raw nuevo)
            raw_nuevo = "".join(filter(str.isdigit, antiguo))
            if len(raw_nuevo) > 8:
                raw_nuevo = raw_nuevo[:8]
        
            # 3) Construimos el string formateado
            nuevo_texto = formatear_ddmmyyyy(raw_nuevo)
        
            # 4) Determinamos la posición en el nuevo texto
            #    Queremos colocar el cursor justo después de dig_antes dígitos
            if dig_antes == 0:
                nueva_pos = 0
            else:
                cont = 0
                nueva_pos = len(nuevo_texto)  # fallback al final
                for i, ch in enumerate(nuevo_texto):
                    if ch.isdigit():
                        cont += 1
                    if cont == dig_antes:
                        # ponemos el cursor justo después de este dígito
                        nueva_pos = i + 1
                        break
        
            # 5) Reemplazamos el contenido y reubicamos el cursor
            entry_fecha.delete(0, "end")
            entry_fecha.insert(0, nuevo_texto)
            entry_fecha.icursor(nueva_pos)
        
        # Asociamos el KeyRelease al entry de fecha
        entry_fecha.bind("<KeyRelease>", on_keyrelease_fecha)

        # --- Recibo ---
        recibo_frame = ttk.Frame(sec1)
        recibo_frame.grid(row=0, column=1, sticky='ew')
        ttk.Label(recibo_frame, text='RECIBO N.°', style='Field.TLabel').pack(side='left', padx=5)

        # Generar el string de recibo: "0001-xxxxxxxx"
        siguiente_id = get_next_cobro_id()
        parte_incremental = f"{siguiente_id:08d}"
        recibo_str = f"{BRANCH_CODE}-{parte_incremental}"
        ttk.Label(recibo_frame, text=recibo_str, style='Field.TLabel').pack(side='left')

        # — 3) Cliente / Pagador —
        sec2 = ttk.Frame(cont, padding=5)
        sec2.pack(fill='x', pady=(0,10))
        ttk.Label(sec2, text='N.° Cliente:',        style='Field.TLabel').grid(row=0, column=0, sticky='w')
        e_cli    = ttk.Entry(sec2, style='Field.TEntry', width=10); e_cli.grid(row=0, column=1, padx=5)
        ttk.Label(sec2, text='Nombre y Apellido:',  style='Field.TLabel').grid(row=0, column=2, padx=10)
        e_nombre = ttk.Entry(sec2, style='Field.TEntry', width=45); e_nombre.grid(row=0, column=3)
        ttk.Label(sec2, text='Fracción:',           style='Field.TLabel').grid(row=0, column=4, padx=10)
        e_par    = ttk.Entry(sec2, style='Field.TEntry', width=10); e_par.grid(row=0, column=5)

        def load_cli(ev=None):
            r = self.clientes.get(e_cli.get().strip())
            e_nombre.delete(0, 'end')
            e_par.delete(0, 'end')
            if r:
                e_nombre.insert(0, r[1])
                e_par.insert(0, r[7] or '')

        e_cli.bind('<FocusOut>', load_cli)
    
        suggest_win = None
        tree_sug = None
        hide_after_id = None

        def hide_suggestions(event=None):
            nonlocal suggest_win, hide_after_id
            if hide_after_id:
                e_nombre.after_cancel(hide_after_id)
                hide_after_id = None
            if suggest_win:
                suggest_win.destroy()
                suggest_win = None

        def hide_suggestions_later(event=None):
            nonlocal hide_after_id
            if hide_after_id:
                e_nombre.after_cancel(hide_after_id)
            hide_after_id = e_nombre.after(150, hide_suggestions)

        def select_suggestion(event=None):
            nonlocal suggest_win
            sel = tree_sug.selection()
            if sel:
                vals = tree_sug.item(sel[0], 'values')
                e_cli.delete(0, 'end')
                e_cli.insert(0, vals[0])
                e_nombre.delete(0, 'end')
                e_nombre.insert(0, vals[1])
                e_par.delete(0, 'end')
                e_par.insert(0, vals[2])
                e_nombre.focus_set()
            hide_suggestions()

        def show_suggestions(event=None):
            nonlocal suggest_win, tree_sug
            query = e_nombre.get().strip().lower()
            if not query:
                hide_suggestions()
                return
            matches = []
            for tup in self.clientes.values():
                name = str(tup[1]).lower()
                pos = name.find(query)
                if pos != -1:
                    matches.append((pos, len(name), tup))
            matches.sort(key=lambda x: (x[0], x[1]))
            matches = [m[2] for m in matches[:5]]
            if not matches:
                hide_suggestions()
                return
            if suggest_win is None:
                suggest_win = tk.Toplevel(self)
                suggest_win.wm_overrideredirect(True)
                suggest_win.attributes('-topmost', True)
                tree_sug = ttk.Treeview(
                    suggest_win,
                    columns=('ID','Nombre','Parcela'),
                    show='headings',
                    height=5
                )
                for c in ('ID','Nombre','Parcela'):
                    tree_sug.heading(c, text=c)
                    tree_sug.column(c, width=120 if c!='Nombre' else 200)
                tree_sug.pack(expand=True, fill='both')
                tree_sug.bind('<ButtonRelease-1>', select_suggestion)
                tree_sug.bind('<Return>', select_suggestion)
                tree_sug.bind('<FocusOut>', hide_suggestions_later)
                tree_sug.bind('<Escape>', lambda e: hide_suggestions())
            else:
                for item in tree_sug.get_children():
                    tree_sug.delete(item)
            for tup in matches:
                tree_sug.insert('', 'end', values=(tup[0], tup[1], tup[7]))
            x = e_nombre.winfo_rootx()
            y = e_nombre.winfo_rooty() + e_nombre.winfo_height()
            suggest_win.geometry(f'+{x}+{y}')
            suggest_win.deiconify()

        e_nombre.bind('<KeyRelease>', show_suggestions)
        e_nombre.bind('<FocusOut>', hide_suggestions_later)

        # — 4) Detalle de Imputaciones —
        det = ttk.Frame(cont, padding=5)
        det.pack(fill='x', pady=(0,10))
        cols = ['N° de Cuenta','Concepto que abona','Importe']
        for j, c in enumerate(cols):
            ttk.Label(det, text=c, style='Field.TLabel', borderwidth=1, relief='solid')\
               .grid(row=0, column=j, sticky='nsew', padx=1)
            det.columnconfigure(j, weight=1)
    
        # Creamos 3 filas (cada fila = [Entry de código, Entry de concepto (readonly), Entry de importe])
        imps = []
        for i in range(1, 4):
            fila = []
            for j in range(3):
                ent = ttk.Entry(det, style='Field.TEntry')
                ent.grid(row=i, column=j, sticky='nsew', padx=1, pady=2)
                # Si es la columna “Concepto” (j == 1), lo dejamos en readonly
                if j == 1:
                    ent.config(state='readonly')
                fila.append(ent)
            imps.append(fila)

        acc_win = None
        acc_tree = None
        acc_hide_id = None

        def hide_acc_popup(event=None):
            nonlocal acc_win, acc_hide_id
            if acc_hide_id:
                e_nombre.after_cancel(acc_hide_id)
                acc_hide_id = None
            if acc_win:
                acc_win.destroy()
                acc_win = None

        def hide_acc_popup_later(event=None):
            nonlocal acc_hide_id
            if acc_hide_id:
                e_nombre.after_cancel(acc_hide_id)
            acc_hide_id = e_nombre.after(150, hide_acc_popup)

        def show_acc_popup(code_entry, name_entry, event=None):
            nonlocal acc_win, acc_tree
            cli_name = e_nombre.get().strip().lower()
            if not cli_name:
                return
            matches = [
                (c, n) for c, n in self.plan.items()
                if cli_name in n.lower()
            ]
            if not matches:
                return
            if acc_win:
                acc_win.destroy()
            acc_win = tk.Toplevel(self)
            acc_win.wm_overrideredirect(True)
            acc_win.attributes('-topmost', True)
            acc_tree = ttk.Treeview(
                acc_win,
                columns=('Cod', 'Nombre'),
                show='headings',
                height=min(len(matches), 5)
            )
            for h, w in (('Cod', 120), ('Nombre', 250)):
                acc_tree.heading(h, text=h)
                acc_tree.column(h, width=w)
            for c, n in matches:
                acc_tree.insert('', 'end', values=(c, n))
            acc_tree.pack(expand=True, fill='both')
            acc_tree.focus_set()

            def choose_account(ev=None):
                sel = acc_tree.selection()
                if sel:
                    cod, nombre = acc_tree.item(sel[0], 'values')
                    code_entry.delete(0, 'end')
                    code_entry.insert(0, cod)
                    name_entry.config(state='normal')
                    name_entry.delete(0, 'end')
                    name_entry.insert(0, nombre)
                    name_entry.config(state='readonly')
                    code_entry.focus_set()
                hide_acc_popup()

            acc_tree.bind('<ButtonRelease-1>', choose_account)
            acc_tree.bind('<Return>', choose_account)
            acc_tree.bind('<Escape>', lambda e: hide_acc_popup())
            acc_tree.bind('<FocusOut>', hide_acc_popup_later)

            x = name_entry.winfo_rootx()
            y = name_entry.winfo_rooty() + name_entry.winfo_height()
            acc_win.geometry(f'+{x}+{y}')   
    
        def fill_con(event, codigo_entry, concepto_entry):
            clave = codigo_entry.get().strip()
            nombre = self.plan.get(clave, '')
            # Abrimos temporalmente el Entry de “Concepto” para insertar el texto
            concepto_entry.config(state='normal')
            concepto_entry.delete(0, 'end')
            concepto_entry.insert(0, nombre)
            concepto_entry.config(state='readonly')
    
        # Enlazar cada Entry de código con fill_con
        for ent_codigo, ent_concepto, ent_importe in imps:
            ent_concepto.bind('<Button-1>', lambda e, c=ent_codigo, o=ent_concepto: show_acc_popup(c, o))
            ent_concepto.bind('<FocusOut>', hide_acc_popup_later)
    
        # — 5) Total — (debajo de las imputaciones)
        ttk.Label(det, text='TOTAL:', style='Field.TLabel').grid(row=4, column=1, sticky='e')
        l_tot = ttk.Label(det, text='0.00', style='Field.TLabel')
        l_tot.grid(row=4, column=2, sticky='e', padx=1)

        # — 5.1) CARGA IMPOSITIVA —
        taxf = ttk.LabelFrame(cont, text='CARGA IMPOSITIVA', padding=5)
        taxf.pack(fill='x', pady=(10,0))
    

        ttk.Label(taxf, text='% IIBB:', style='Field.TLabel').grid(row=0, column=0, sticky='e')
        e_iibb = ttk.Entry(taxf, style='Field.TEntry', width=10, state='readonly')
        e_iibb.grid(row=0, column=1, sticky='w', padx=(5,15))
    
        ttk.Label(taxf, text='% DByCR:', style='Field.TLabel').grid(row=0, column=2, sticky='e')
        e_iibb.grid(row=0, column=1, sticky='w', padx=(5,10))
        ttk.Label(taxf, text='Importe:', style='Field.TLabel').grid(row=0, column=2, sticky='e')
        l_iibb = ttk.Label(taxf, text='0.00', style='Field.TLabel')
        l_iibb.grid(row=0, column=3, sticky='w', padx=(5,15))

        ttk.Label(taxf, text='% DByCR:', style='Field.TLabel').grid(row=1, column=0, sticky='e')
        e_dby = ttk.Entry(taxf, style='Field.TEntry', width=10, state='readonly')

        e_dby.grid(row=1, column=1, sticky='w', padx=(5,10))
        ttk.Label(taxf, text='Importe:', style='Field.TLabel').grid(row=1, column=2, sticky='e')
        l_dby = ttk.Label(taxf, text='0.00', style='Field.TLabel')
        l_dby.grid(row=1, column=3, sticky='w', padx=(5,15))

        ttk.Label(taxf, text='% IVA:', style='Field.TLabel').grid(row=2, column=0, sticky='e')
        e_iva = ttk.Entry(taxf, style='Field.TEntry', width=10, state='readonly')

        # — 5.3) CAJA O CUENTA BANCARIA DONDE INGRESA EL PAGO —
        ttk.Label(
            cont,
            text='CAJA O CUENTA BANCARIA DONDE INGRESA EL PAGO',
            style='Field.TLabel'
        ).pack(fill='x', pady=(5,0))

        # — 6) Cuentas A/B y Observaciones —
        box_ab = ttk.Frame(cont, padding=5)
        box_ab.pack(fill='x', pady=(0,10))
        
        ttk.Label(box_ab, text='Cuenta A:', style='Field.TLabel').grid(row=0, column=0, sticky='w')
        ca = ttk.Entry(box_ab, style='Field.TEntry', width=12); ca.grid(row=0, column=1, padx=5)
        ttk.Label(box_ab, text='Detalle A:', style='Field.TLabel').grid(row=0, column=2, padx=10)
        da = ttk.Entry(box_ab, style='Field.TEntry', width=25, state='readonly'); da.grid(row=0, column=3)
        ttk.Label(box_ab, text='Monto A:', style='Field.TLabel').grid(row=0, column=4, padx=10)
        ma = ttk.Entry(box_ab, style='Field.TEntry', width=10); ma.grid(row=0, column=5)
    
        ttk.Label(box_ab, text='Cuenta B:', style='Field.TLabel').grid(row=1, column=0, sticky='w', pady=5)
        cb = ttk.Entry(box_ab, style='Field.TEntry', width=12); cb.grid(row=1, column=1, padx=5)
        ttk.Label(box_ab, text='Detalle B:', style='Field.TLabel').grid(row=1, column=2, padx=10, pady=5)
        db = ttk.Entry(box_ab, style='Field.TEntry', width=25, state='readonly'); db.grid(row=1, column=3, pady=5)
        ttk.Label(box_ab, text='Monto B:', style='Field.TLabel').grid(row=1, column=4, padx=10, pady=5)
        mb = ttk.Entry(box_ab, style='Field.TEntry', width=10); mb.grid(row=1, column=5, pady=5)
    
        ttk.Label(box_ab, text='Observaciones:', style='Field.TLabel').grid(row=2, column=0, sticky='nw', pady=10)
        obs = ttk.Entry(box_ab, style='Field.TEntry', width=50)
        obs.grid(row=2, column=1, columnspan=5, sticky='ew', pady=10)
    
        def fill_acc(e, det_ent):
            code = e.widget.get().strip()
            det_ent.config(state='normal')
            det_ent.delete(0, 'end')
            det_ent.insert(0, self.plan.get(code, ''))
            det_ent.config(state='readonly')
    
        # Autocompletar “Detalle A” / “Detalle B”
        ca.bind('<FocusOut>',  lambda e: fill_acc(e, da))
        ca.bind('<KeyRelease>', lambda e: fill_acc(e, da))
        cb.bind('<FocusOut>',  lambda e: fill_acc(e, db))
        cb.bind('<KeyRelease>', lambda e: fill_acc(e, db))

        cash_win = None
        cash_tree = None
        cash_hide_id = None

        def hide_cash_popup(event=None):
            nonlocal cash_win, cash_hide_id
            if cash_hide_id:
                self.after_cancel(cash_hide_id)
                cash_hide_id = None
            if cash_win:
                cash_win.destroy()
                cash_win = None

        def hide_cash_popup_later(event=None):
            nonlocal cash_hide_id
            if cash_hide_id:
                self.after_cancel(cash_hide_id)
            cash_hide_id = self.after(150, hide_cash_popup)

        def show_cash_popup(code_entry, name_entry, event=None):
            nonlocal cash_win, cash_tree
            taxes = load_tax_cobros()
            matches = [
                (c, self.plan.get(c, ''), taxes[c][0], taxes[c][1])
                for c in taxes
            ]
            if not matches:
                return
            if cash_win:
                cash_win.destroy()
            cash_win = tk.Toplevel(self)
            cash_win.wm_overrideredirect(True)
            cash_win.attributes('-topmost', True)
            cash_tree = ttk.Treeview(
                cash_win,
                columns=('Cod', 'Nombre', '%IIBB', '%DByCR'),
                show='headings',
                height=min(len(matches), 5),
            )
            for h, w in (('Cod', 100), ('Nombre', 200), ('%IIBB', 60), ('%DByCR', 60)):
                cash_tree.heading(h, text=h)
                cash_tree.column(h, width=w, anchor='center')
            for c, n, p_i, p_d in matches:
                cash_tree.insert('', 'end', values=(c, n, f"{p_i:.2f}", f"{p_d:.2f}"))
            cash_tree.pack(expand=True, fill='both')
            cash_tree.focus_set()

            def choose_cash(ev=None):
                sel = cash_tree.selection()
                if sel:
                    vals = cash_tree.item(sel[0], 'values')
                    cod, nombre = vals[0], vals[1]
                    code_entry.delete(0, 'end')
                    code_entry.insert(0, cod)
                    name_entry.config(state='normal')
                    name_entry.delete(0, 'end')
                    name_entry.insert(0, nombre)
                    name_entry.config(state='readonly')
                    code_entry.focus_set()
                    upd_tot()  # actualizar porcentajes e importes
                hide_cash_popup()

            cash_tree.bind('<ButtonRelease-1>', choose_cash)
            cash_tree.bind('<Return>', choose_cash)
            cash_tree.bind('<Escape>', lambda e: hide_cash_popup())
            cash_tree.bind('<FocusOut>', hide_cash_popup_later)

            x = name_entry.winfo_rootx()
            y = name_entry.winfo_rooty() + name_entry.winfo_height()
            cash_win.geometry(f'+{x}+{y}')

        # Enlazar popups después de definir la lógica
        da.bind('<Button-1>', lambda e: show_cash_popup(ca, da))
        da.bind('<FocusOut>', hide_cash_popup_later)
        db.bind('<Button-1>', lambda e: show_cash_popup(cb, db))
        db.bind('<FocusOut>', hide_cash_popup_later)
    
            # — 7) Recalcular Totales e Impuestos en cada cambio —
        def upd_tot(e=None):
            try:
                # 1) (Opcional) Subtotal de imputaciones
                subtotal_imput = sum(float(r[2].get() or 0) for r in imps)
                l_tot.config(text=f"{subtotal_imput:.2f}")
    
                # 2) Obtener porcentajes IIBB / DByCR para Cuenta A y Cuenta B
                tbl = load_tax_cobros()
                pA_iibb, pA_dbcr = tbl.get(ca.get().strip(), (0.0, 0.0))
                pB_iibb, pB_dbcr = tbl.get(cb.get().strip(), (0.0, 0.0))
    
                # 3) Leer montos numéricos “Monto A” y “Monto B”
                try:
                    montoA_val = float(ma.get() or 0)
                except ValueError:
                    montoA_val = 0.0
                try:
                    montoB_val = float(mb.get() or 0)
                except ValueError:
                    montoB_val = 0.0
    
                # 4) Calcular IIBB y DByCR sobre Monto A y Monto B
                monto_iibb_A  = montoA_val * (pA_iibb / 100)
                monto_dbcr_A  = montoA_val * (pA_dbcr / 100)
                monto_iibb_B  = montoB_val * (pB_iibb / 100)
                monto_dbcr_B  = montoB_val * (pB_dbcr / 100)
    
                # 5) Calcular IVA (21%) **sobre el monto de cada cuenta**, no sobre el subtotal de imputaciones
                pct_iva = 21.0
                base_sin_iva = subtotal_imput / 1.21 if subtotal_imput else 0.0
                monto_iva = subtotal_imput - base_sin_iva
    
                # 6) Mostrar los porcentajes combinados (suman de A+B)
                total_pct_iibb = pA_iibb + pB_iibb
                total_pct_dbcr = pA_dbcr + pB_dbcr
    
                e_iibb.config(state='normal')
                e_iibb.delete(0, 'end')
                e_iibb.insert(0, f"{total_pct_iibb:.2f}")
                e_iibb.config(state='readonly')
    
                e_dby.config(state='normal')
                e_dby.delete(0, 'end')
                e_dby.insert(0, f"{total_pct_dbcr:.2f}")
                e_dby.config(state='readonly')
    
                e_iva.config(state='normal')
                e_iva.delete(0, 'end')
                e_iva.insert(0, f"{pct_iva:.2f}")
                e_iva.config(state='readonly')
    
                l_iibb.config(text=f"{monto_iibb_A + monto_iibb_B:.2f}")
                l_dby.config(text=f"{monto_dbcr_A + monto_dbcr_B:.2f}")
                l_iva.config(text=f"{monto_iva:.2f}")
                # 7) Total con impuestos:
                #    - montoA + montoB
                #    - más impuestos IIBB y DByCR correspondientes a A y B
                #    - más IVA correspondiente a A y B
                total_con_imp = (
                    montoA_val + montoB_val
                    + monto_iibb_A + monto_iibb_B
                    + monto_dbcr_A + monto_dbcr_B
                    + monto_iva
                )
    
            except Exception:
                # Si ocurre cualquier error (por ej. campo vacío), no interrumpe la app
                pass
    
        # Vincular eventos a upd_tot (DEBE SER DESPUÉS de definirla)
        for _, _, ent_importe in imps:
            ent_importe.bind('<KeyRelease>', upd_tot)
        ca.bind('<KeyRelease>', upd_tot)
        ma.bind('<KeyRelease>', upd_tot)
        cb.bind('<KeyRelease>', upd_tot)
        mb.bind('<KeyRelease>', upd_tot)

    
        # — 8) Botón Guardar Cobro —
        ttk.Button(cont, text='Guardar Cobro', style='Big.TButton',
                   command=lambda: (
                       self._save_cobro(
                           entry_fecha.get(),
                           e_nombre.get(), e_par.get(),
                           [
                               (imps[i][0].get(), imps[i][1].get(), float(imps[i][2].get() or 0))
                               for i in range(3)
                           ],
                           ca.get(), ma.get(),
                           cb.get(), mb.get(),
                           obs.get()
                       )
                   )).pack(pady=15)




    def _save_cobro(self, fecha, nombre_cli, parcela, imputaciones,
                    cuentaA, montoA, cuentaB, montoB, obs):
        total_imputaciones = sum(imp[2] for imp in imputaciones)
        montoA_val = float(montoA or 0)
        montoB_val = float(montoB or 0)

        if round(total_imputaciones, 2) != round(montoA_val + montoB_val, 2):
            messagebox.showerror(
                'Error',
                'La suma de "Monto A" y "Monto B" debe coincidir con el total de imputaciones.'
            )
            return
        # Leer porcentajes de cuentaA y cuentaB
        tbl = load_tax_cobros()
        pA_iibb, pA_dbcr = tbl.get(cuentaA.strip(), (0.0, 0.0))
        pB_iibb, pB_dbcr = tbl.get(cuentaB.strip(), (0.0, 0.0))

        # Montos de impuestos IIBB / DByCR por cuenta
        monto_iibb_A  = montoA_val * (pA_iibb  / 100)
        monto_dbcr_A  = montoA_val * (pA_dbcr  / 100)
        monto_iibb_B  = montoB_val * (pB_iibb  / 100)
        monto_dbcr_B  = montoB_val * (pB_dbcr  / 100)

        monto_iibb = monto_iibb_A + monto_iibb_B
        monto_dbcr = monto_dbcr_A + monto_dbcr_B

        # IVA 21% **sobre montoA y montoB**, no sobre total de imputaciones
        pct_iva = 21.0
        base_sin_iva = total_imputaciones / 1.21 if total_imputaciones else 0.0
        iva_val = total_imputaciones - base_sin_iva

        # Construir el objeto cobro con los impuestos ya en pesos
        c = cobro(
            get_next_cobro_id(),
            fecha,
            nombre_cli,
            parcela,
            # … campos de imputaciones …
            imputaciones[0][0], imputaciones[0][1], imputaciones[0][2],
            imputaciones[1][0], imputaciones[1][1], imputaciones[1][2],
            imputaciones[2][0], imputaciones[2][1], imputaciones[2][2],
            cuentaA, montoA_val,
            cuentaB, montoB_val,
            monto_dbcr,   # DByCR en pesos (A+B)
            monto_iibb,   # IIBB en pesos (A+B)
            iva_val,      # IVA en pesos (A+B)
            obs
        )
        save_cobros((c,))
        messagebox.showinfo('Éxito', 'Cobro guardado.')
        self._load_data()
        self._show_frame('lst_cobros')





    def _build_pago(self, parent):
        # 1) Limpiar contenido anterior
        for w in parent.winfo_children():
            w.destroy()

        # 2) Contenedor principal centrado
        cont = ttk.Frame(parent, padding=20, relief='groove')
        cont.place(relx=0.5, rely=0.5, anchor='center')

        # 3) Título
        ttk.Label(cont, text='Registro Egreso', style='Title.TLabel')\
            .pack(pady=(0,20))

        # 4) Fecha y Número de Pago
        sec1 = ttk.Frame(cont, padding=5)
        sec1.pack(fill='x', pady=(0,10))
        sec1.grid_columnconfigure(0, weight=1)
        sec1.grid_columnconfigure(1, weight=1)

        ttk.Label(sec1, text='Fecha:', style='Field.TLabel')\
           .grid(row=0, column=0, sticky='e', padx=(0,5))
        fecha_entry = ttk.Entry(sec1, style='Field.TEntry', width=15)
        fecha_entry.grid(row=0, column=1, sticky='w')

        ttk.Label(sec1, text='PAGO N.°:', style='Field.TLabel')\
           .grid(row=0, column=2, sticky='e', padx=(20,5))
        ttk.Label(sec1, text=str(get_next_pago_id()), style='Field.TLabel')\
           .grid(row=0, column=3, sticky='w')

        # 5) Datos del beneficiario
        sec2 = ttk.Frame(cont, padding=5)
        sec2.pack(fill='x', pady=(0,10))

        ttk.Label(sec2, text='Pagado a (Razón Social):', style='Field.TLabel')\
           .grid(row=0, column=0, sticky='e', padx=(0,5))
        razon_entry = ttk.Entry(sec2, style='Field.TEntry', width=40)
        razon_entry.grid(row=0, column=1, columnspan=3, sticky='w')

        ttk.Label(sec2, text='Concepto:', style='Field.TLabel')\
           .grid(row=1, column=0, sticky='e', pady=(5,0), padx=(0,5))
        concepto_entry = ttk.Entry(sec2, style='Field.TEntry', width=60)
        concepto_entry.grid(row=1, column=1, columnspan=3, sticky='w', pady=(5,0))

        ttk.Label(sec2, text='Tipo y N.°:', style='Field.TLabel')\
           .grid(row=2, column=0, sticky='e', pady=(5,0), padx=(0,5))
        tipo_entry = ttk.Entry(sec2, style='Field.TEntry', width=30)
        tipo_entry.grid(row=2, column=1, columnspan=3, sticky='w', pady=(5,0))

        # 6) Tabla de imputación / pagos
        sec3 = ttk.Frame(cont, padding=5)
        sec3.pack(fill='x', pady=(0,10))
        headers = ['Cuenta (Imp.)','Denominación','Importe Neto']
        for j, h in enumerate(headers):
            ttk.Label(sec3, text=h, style='Field.TLabel', borderwidth=1, relief='solid')\
               .grid(row=0, column=j, sticky='nsew', padx=1)
            sec3.columnconfigure(j, weight=1)

        # --- Fila de imputación (sin impuestos) ---
        imput_cuenta = ttk.Entry(sec3, style='Field.TEntry')
        imput_cuenta.grid(row=1, column=0, sticky='nsew', padx=1, pady=2)

        imput_denom = ttk.Entry(sec3, style='Field.TEntry', state='readonly')
        imput_denom.grid(row=1, column=1, sticky='nsew', padx=1, pady=2)

        imput_imp = ttk.Entry(sec3, style='Field.TEntry')
        imput_imp.grid(row=1, column=2, sticky='nsew', padx=1, pady=2)

        # --- Fila “paga” (cuenta que paga / impuestos) ---
        ttk.Label(sec3, text='Cuenta A (para impuestos):', style='Field.TLabel', borderwidth=1, relief='solid')\
           .grid(row=2, column=0, sticky='nsew', padx=1)

        pago_cuenta = ttk.Entry(sec3, style='Field.TEntry')
        pago_cuenta.grid(row=3, column=0, sticky='nsew', padx=1, pady=2)

        pago_denom = ttk.Entry(sec3, style='Field.TEntry', state='readonly')
        pago_denom.grid(row=3, column=1, sticky='nsew', padx=1, pady=2)

        # — Campos de porcentaje y total impuesto — 
        ttk.Label(sec3, text='% DByCR:', style='Field.TLabel')\
           .grid(row=2, column=2, sticky='e', padx=(5,1))
        e_dbcr_pct = ttk.Entry(sec3, style='Field.TEntry', width=10, state='readonly')
        e_dbcr_pct.grid(row=2, column=3, sticky='w', padx=(1,0))

        ttk.Label(sec3, text='% IVA:', style='Field.TLabel')\
           .grid(row=3, column=2, sticky='e', padx=(5,1))
        e_iva_pct = ttk.Entry(sec3, style='Field.TEntry', width=10, state='readonly')
        e_iva_pct.grid(row=3, column=3, sticky='w', padx=(1,0))

        # — Campo de Total con Impuestos — 
        ttk.Label(sec3, text='TOTAL c/ Impuestos:', style='Field.TLabel')\
           .grid(row=4, column=1, sticky='e', pady=(10,0))
        l_total_imp = ttk.Label(sec3, text='0.00', style='Field.TLabel')
        l_total_imp.grid(row=4, column=2, columnspan=2, sticky='w', pady=(10,0), padx=(5,0))

        # 7) Autocompletar denominaciones y calcular impuestos
        def fill_imput(e):
            code = imput_cuenta.get().strip()
            name = self.plan.get(code, '')
            imput_denom.config(state='normal')
            imput_denom.delete(0, 'end')
            imput_denom.insert(0, name)
            imput_denom.config(state='readonly')

        imput_cuenta.bind('<FocusOut>', fill_imput)
        imput_cuenta.bind('<KeyRelease>', fill_imput)

        def fill_pago(e):
            code = pago_cuenta.get().strip()
            name = self.plan.get(code, '')
            pago_denom.config(state='normal')
            pago_denom.delete(0, 'end')
            pago_denom.insert(0, name)
            pago_denom.config(state='readonly')
            # Cuando cambia la cuenta, recalculemos impuestos
            upd_tot()

        pago_cuenta.bind('<FocusOut>', fill_pago)
        pago_cuenta.bind('<KeyRelease>', fill_pago)

        def upd_tot(e=None):
            try:
                # 1) Leer el monto neto que se va a pagar
                try:
                    neto_val = float(imput_imp.get() or 0)
                except ValueError:
                    neto_val = 0.0

                # 2) Obtener porcentaje DByCR de la tabla de pagos
                tblp = load_tax_pagos()  # dict: { 'cuenta': pct_dbcr }
                pct_dbcr = tblp.get(pago_cuenta.get().strip(), 0.0)

                # 3) Calcular IVA (21%) sobre el neto
                pct_iva = 21.0
                base_sin_iva = neto_val / 1.21 if neto_val else 0.0
                monto_iva = neto_val - base_sin_iva

                # 4) Calcular Monto DByCR bancario
                monto_dbcr = neto_val * (pct_dbcr / 100)

                # 5) Mostrar porcentajes
                e_dbcr_pct.config(state='normal')
                e_dbcr_pct.delete(0, 'end')
                e_dbcr_pct.insert(0, f"{pct_dbcr:.2f}")
                e_dbcr_pct.config(state='readonly')

                e_iva_pct.config(state='normal')
                e_iva_pct.delete(0, 'end')
                e_iva_pct.insert(0, f"{pct_iva:.2f}")
                e_iva_pct.config(state='readonly')

                # 6) Total con impuestos = neto + IVA + DByCR
                total_imp = neto_val + monto_dbcr
                l_total_imp.config(text=f"{total_imp:.2f}")
            except Exception:
                pass

        imput_imp.bind('<KeyRelease>', upd_tot)

        # 8) Botón “Guardar Pago”
        ttk.Button(cont, text='Guardar Pago', style='Big.TButton',
                   command=lambda: (
                       self._save_pago(
                           fecha_entry.get(),
                           razon_entry.get(),
                           concepto_entry.get(),
                           tipo_entry.get(),
                           imput_cuenta.get().strip(),       # cuenta imputación (sin impuesto)
                           float(imput_imp.get() or 0),      # monto neto
                           pago_cuenta.get().strip(),        # cuenta A para impuestos
                           None                              # si deseas, puedes agregar un campo de observaciones
                       )
                   )).pack(pady=15)


    def _save_pago(self, fecha, razon, concepto, tipo, cod_cuenta, monto_neto, cod_paga, obs):
        # 1) Obtener porcentaje DByCR bancario de la cuenta A
        tblp = load_tax_pagos()  # dict: { 'cuenta': pct_dbcr }
        pct_dbcr = tblp.get(cod_paga.strip(), 0.0)

        # 2) Calcular montos de impuestos sobre el neto
        base_sin_iva = monto_neto / 1.21 if monto_neto else 0.0
        monto_iva_val  = monto_neto - base_sin_iva

        # 3) Crear objeto pago con los valores en pesos
        p = pago(
            get_next_pago_id(),
            fecha,
            razon,
            concepto,
            tipo,
            cod_cuenta,         # cuenta imputación
            monto_neto,         # importe neto
            monto_iva_val,      # importe IVA en pesos
            cod_paga,           # cuenta que paga (para impuesto bancario)
            monto_dbcr_val      # importe DByCR en pesos
        )
        save_pagos((p,))
        messagebox.showinfo('Éxito', 'Pago registrado.')
        self._show_frame('lst_pagos')




    def _build_cliente(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        cont = ttk.Frame(parent, padding=20, relief='groove')
        cont.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(cont, text='Registro de Cliente', style='Title.TLabel').pack(pady=(0,20))

        fields = ttk.Frame(cont)
        fields.pack()

        ttk.Label(fields, text='Nombre y Apellido:', style='Field.TLabel')\
            .grid(row=0, column=0, sticky='e', padx=5, pady=5)
        nombre_entry = ttk.Entry(fields, style='Field.TEntry', width=45)
        nombre_entry.grid(row=0, column=1, columnspan=3, pady=5)

        ttk.Label(fields, text='DNI:', style='Field.TLabel')\
            .grid(row=1, column=0, sticky='e', padx=5, pady=5)
        dni_entry = ttk.Entry(fields, style='Field.TEntry', width=20)
        dni_entry.grid(row=1, column=1, pady=5)

        ttk.Label(fields, text='Dirección:', style='Field.TLabel')\
            .grid(row=1, column=2, sticky='e', padx=5, pady=5)
        direccion_entry = ttk.Entry(fields, style='Field.TEntry', width=30)
        direccion_entry.grid(row=1, column=3, pady=5)

        ttk.Label(fields, text='Email:', style='Field.TLabel')\
            .grid(row=2, column=0, sticky='e', padx=5, pady=5)
        email_entry = ttk.Entry(fields, style='Field.TEntry', width=25)
        email_entry.grid(row=2, column=1, columnspan=3, pady=5, sticky='w')

        ttk.Label(fields, text='Teléfono 1:', style='Field.TLabel')\
            .grid(row=3, column=0, sticky='e', padx=5, pady=5)
        tel1_entry = ttk.Entry(fields, style='Field.TEntry', width=15)
        tel1_entry.grid(row=3, column=1, pady=5)

        ttk.Label(fields, text='Teléfono 2:', style='Field.TLabel')\
            .grid(row=3, column=2, sticky='e', padx=5, pady=5)
        tel2_entry = ttk.Entry(fields, style='Field.TEntry', width=15)
        tel2_entry.grid(row=3, column=3, pady=5)

        ttk.Label(fields, text='Parcela 1:', style='Field.TLabel')\
            .grid(row=4, column=0, sticky='e', padx=5, pady=5)
        parcela1_entry = ttk.Entry(fields, style='Field.TEntry', width=10)
        parcela1_entry.grid(row=4, column=1, pady=5)

        ttk.Label(fields, text='Parcela 2:', style='Field.TLabel')\
            .grid(row=4, column=2, sticky='e', padx=5, pady=5)
        parcela2_entry = ttk.Entry(fields, style='Field.TEntry', width=10)
        parcela2_entry.grid(row=4, column=3, pady=5)

        ttk.Label(fields, text='Parcela 3:', style='Field.TLabel')\
            .grid(row=5, column=0, sticky='e', padx=5, pady=5)
        parcela3_entry = ttk.Entry(fields, style='Field.TEntry', width=10)
        parcela3_entry.grid(row=5, column=1, pady=5)

        ttk.Label(fields, text='Superficie:', style='Field.TLabel')\
            .grid(row=5, column=2, sticky='e', padx=5, pady=5)
        superficie_entry = ttk.Entry(fields, style='Field.TEntry', width=10)
        superficie_entry.grid(row=5, column=3, pady=5)

        ttk.Label(fields, text='Observación:', style='Field.TLabel')\
            .grid(row=6, column=0, sticky='ne', padx=5, pady=(10,5))
        observacion_entry = ttk.Entry(fields, style='Field.TEntry', width=50)
        observacion_entry.grid(row=6, column=1, columnspan=3, pady=(10,5), sticky='w')

        ttk.Button(cont, text='Guardar Cliente', style='Big.TButton',
                   command=lambda: (
                       self._save_cliente(
                           nombre_entry.get(),
                           dni_entry.get(),
                           direccion_entry.get(),
                           tel1_entry.get(),
                           tel2_entry.get(),
                           email_entry.get(),
                           parcela1_entry.get(),
                           parcela2_entry.get(),
                           parcela3_entry.get(),
                           superficie_entry.get(),
                           observacion_entry.get()
                       )
                   )).pack(pady=(20,0))


    def _save_cliente(self, nombre, dni, direccion, t1, t2, email, p1, p2, p3, sup, obs):
        c = cliente(
            get_next_clients_id(),
            nombre, dni, direccion,
            t1, t2, email,
            p1, p2, p3,
            sup, obs
        )
        save_clients((c,))
        messagebox.showinfo('Éxito', 'Cliente registrado.')
        self._show_frame('lst_clientes')


    def _build_plan(self, parent):
        # Limpiar todo
        for w in parent.winfo_children():
            w.destroy()

        cont = ttk.Frame(parent, padding=10)
        cont.pack(expand=True, fill='both')

        # — TÍTULO (row=0) —
        lbl_title = ttk.Label(cont, text='Plan de Cuentas', style='Title.TLabel')
        lbl_title.grid(row=0, column=0, columnspan=2, pady=(0,10))

        # Leo todas las cuentas
        full_path = os.path.join(ensure_data_directory(), 'plan_cuentas.txt')
        regs = load_plan_cuentas()  # [(numCuenta, nombre), ...]

        if not regs:
            lbl_empty = ttk.Label(cont, text='No hay cuentas.', style='Field.TLabel')
            lbl_empty.grid(row=1, column=0, columnspan=2, pady=20)
            return

        # Columnas: Num cuenta, Nombre
        cols = ['Num cuenta', 'Nombre']

        # PREPARAMOS GRID COLUMNS = 2
        cont.grid_columnconfigure(0, weight=1)

        # Frame de tabla con filtros y treeview
        table = ttk.Frame(cont)
        table.grid(row=1, column=0, sticky='nsew', columnspan=len(cols))
        cont.grid_rowconfigure(1, weight=1)

        filtro_canvas = tk.Canvas(table, highlightthickness=0)
        filtro_canvas.grid(row=0, column=0, columnspan=len(cols), sticky='ew')
        filtro_canvas.configure(xscrollcommand=lambda *a: hsb.set(*a))

        filtro_frame = ttk.Frame(filtro_canvas)
        filtro_canvas.create_window((0, 0), window=filtro_frame, anchor='nw')

        # — FILTROS (row=1) — uno por cada columna
        filtro_entrys = {}
        for col_idx, col_name in enumerate(cols):
            ent = PlaceholderEntry(filtro_frame, placeholder=col_name, style='Field.TEntry')
            ent.grid(row=0, column=col_idx, padx=1, sticky='ew')
            filtro_frame.grid_columnconfigure(col_idx, weight=1)
            filtro_entrys[col_idx] = ent

        # — TREEVIEW + SCROLLBARS (row=2) —
        filtro_canvas.update_idletasks()
        filtro_canvas.configure(scrollregion=filtro_canvas.bbox('all'))

        vsb = ttk.Scrollbar(table, orient='vertical')
        hsb = ttk.Scrollbar(table, orient='horizontal')

        def _tree_xview(*args):
            filtro_canvas.xview_moveto(args[0])
            hsb.set(*args)

        tree = ttk.Treeview(
            table,
            columns=cols,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=_tree_xview
        )
        vsb.config(command=tree.yview)

        # Ubicamos el Treeview en row=2, columna 0..1
        def _scroll_x(*args):
            tree.xview(*args)
            filtro_canvas.xview(*args)

        hsb.config(command=_scroll_x)

        # Hacemos que el Treeview crezca verticalmente
        tree.grid(row=1, column=0, columnspan=len(cols), sticky='nsew', pady=(5,0))
        vsb.grid(row=1, column=len(cols), sticky='ns', pady=(5,0))
        hsb.grid(row=2, column=0, columnspan=len(cols), sticky='ew')

        table.grid_rowconfigure(1, weight=1)

        for c in cols:
            tree.heading(c, text=c, anchor='center')
            tree.column(c, width=150, anchor='center')

        # Función para llenar el Treeview
        def poblar_plan(lista):
            for item in tree.get_children():
                tree.delete(item)
            for row in lista:
                tree.insert('', 'end', values=row)

        poblar_plan(regs)

        # Función de filtrado (se aplica sobre cada columna en su índice correspondiente)
        def aplicar_filtros_plan(event=None):
            filtros = {idx: ent.get() for idx, ent in filtro_entrys.items()}
            filtrados = []
            for row in regs:
                match = True
                for col_idx, txt in filtros.items():
                    if txt.strip() == "":
                        continue
                    if txt.lower() not in str(row[col_idx]).lower():
                        match = False
                        break
                if match:
                    filtrados.append(row)
            poblar_plan(filtrados)

        for ent in filtro_entrys.values():
            ent.bind('<KeyRelease>', aplicar_filtros_plan)

        # Botón “Eliminar cuenta seleccionada” (row=4)
        btn_frame = ttk.Frame(cont)
        btn_frame.grid(row=2, column=0, sticky='w', pady=(10,0))
        btn_elim = ttk.Button(btn_frame, text='Eliminar cuenta seleccionada', style='Big.TButton')
        btn_elim.grid(row=0, column=0, padx=5)
        btn_edit = ttk.Button(btn_frame, text='Editar cuenta seleccionada', style='Big.TButton')
        btn_edit.grid(row=0, column=1, padx=5)

        def eliminar_plan():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione una cuenta.')
                return
            valores = tree.item(sel[0], 'values')
            num_cuenta = valores[0]
            if not messagebox.askyesno('Confirmar', f'¿Eliminar cuenta {num_cuenta}?'):
                return

            actuales = load_plan_cuentas()
            nuevos = [r for r in actuales if str(r[0]) != str(num_cuenta)]
            overwrite_records(full_path, nuevos)

            nonlocal regs
            regs = nuevos
            aplicar_filtros_plan()

        btn_elim.config(command=eliminar_plan)

        def editar_plan():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione una cuenta.')
                return
            vals = tree.item(sel[0], 'values')
            num_cuenta = vals[0]
            idx_reg = None
            for i, r in enumerate(regs):
                if str(r[0]) == str(num_cuenta):
                    idx_reg = i
                    break
            if idx_reg is None:
                return

            orig_row = list(regs[idx_reg])

            win = tk.Toplevel(self)
            win.title('Editar cuenta')
            ttk.Label(win, text='Num cuenta:', style='Field.TLabel').grid(row=0, column=0, sticky='e', padx=5, pady=2)
            e_num = ttk.Entry(win, style='Field.TEntry')
            e_num.grid(row=0, column=1, padx=5, pady=2)
            e_num.insert(0, vals[0])
            ttk.Label(win, text='Nombre:', style='Field.TLabel').grid(row=1, column=0, sticky='e', padx=5, pady=2)
            e_nom = ttk.Entry(win, style='Field.TEntry')
            e_nom.grid(row=1, column=1, padx=5, pady=2)
            e_nom.insert(0, vals[1])

            def guardar():
                regs[idx_reg] = (e_num.get(), e_nom.get())
                overwrite_records(full_path, regs)
                self._load_data()
                aplicar_filtros_plan()
                win.destroy()

            ttk.Button(win, text='Guardar', command=guardar, style='Big.TButton').grid(row=2, column=0, columnspan=2, pady=10)

        btn_edit.config(command=editar_plan)

        # Formulario para agregar nuevas cuentas (row=5)
        frm2 = ttk.Frame(cont, padding=5)
        frm2.grid(row=3, column=0, sticky='ew', pady=(10,0))
        ttk.Label(frm2, text='Num cuenta:', style='Field.TLabel').grid(row=0, column=0)
        cde = ttk.Entry(frm2, style='Field.TEntry')
        cde.grid(row=0, column=1, padx=(5,20))
        ttk.Label(frm2, text='Nombre:', style='Field.TLabel').grid(row=0, column=2)
        cna = ttk.Entry(frm2, style='Field.TEntry')
        cna.grid(row=0, column=3, padx=(5,0))
        ttk.Button(frm2, text='Agregar', style='Big.TButton',
            command=lambda: (
                save_plan_cuentas(((cde.get(), cna.get()),)),
                messagebox.showinfo('Éxito', 'Cuenta agregada.'),
                self._load_data(),
                self._show_frame('plan')
            )
        ).grid(row=1, column=0, columnspan=4, pady=(10,0))

    def _build_tax_cobros(self, parent):
        # 0) Limpiar todo
        for w in parent.winfo_children():
            w.destroy()

        # 1) Título principal
        ttk.Label(parent, text='Tabla Impositiva - Cobros', style='Title.TLabel').pack(pady=10)

        # 2) Sub-Frame donde usaremos grid
        cont = ttk.Frame(parent, padding=10)
        cont.pack(expand=True, fill='both')

        # 3) Leo registros de disco
        full_path = os.path.join(ensure_data_directory(), 'tax_cobros.txt')
        tbl = load_tax_cobros()  # dict { 'cuenta': (iibb, dbcr) }
        regs = [(num, *tbl[num]) for num in tbl]
        # regs = [(cuenta, iibb_pct, dbcr_pct), ...]

        # 4) Columnas definidas (se mostrarán: Cuenta, Nombre, %IIBB, %DByCR)
        cols = ['Cuenta', 'Nombre', '%IIBB', '%DByCR']

        cont.grid_columnconfigure(0, weight=1)

        table = ttk.Frame(cont)
        table.grid(row=0, column=0, sticky='nsew')
        cont.grid_rowconfigure(0, weight=1)

        filtro_canvas = tk.Canvas(table, highlightthickness=0)
        filtro_canvas.grid(row=0, column=0, columnspan=len(cols), sticky='ew')
        filtro_canvas.configure(xscrollcommand=lambda *a: hsb.set(*a))

        filtro_frame = ttk.Frame(filtro_canvas)
        filtro_canvas.create_window((0, 0), window=filtro_frame, anchor='nw')

        # — FILTROS (row=0) — solamente para las dos primeras columnas
        filtro_entrys = {}
        ent_cuenta = PlaceholderEntry(filtro_frame, placeholder='Cuenta', style='Field.TEntry')
        ent_cuenta.grid(row=0, column=0, padx=1, pady=(0,5), sticky='ew')
        filtro_frame.grid_columnconfigure(0, weight=1)
        filtro_entrys[0] = ent_cuenta

        ent_nombre = PlaceholderEntry(filtro_frame, placeholder='Nombre', style='Field.TEntry')
        ent_nombre.grid(row=0, column=1, padx=1, pady=(0,5), sticky='ew')
        filtro_frame.grid_columnconfigure(1, weight=1)
        filtro_entrys[1] = ent_nombre

        ttk.Label(filtro_frame, text='').grid(row=0, column=2, padx=1, pady=(0,5))
        ttk.Label(filtro_frame, text='').grid(row=0, column=3, padx=1, pady=(0,5))

        filtro_canvas.update_idletasks()
        filtro_canvas.configure(scrollregion=filtro_canvas.bbox('all'))

        vsb = ttk.Scrollbar(table, orient='vertical')
        hsb = ttk.Scrollbar(table, orient='horizontal')

        def _tree_xview(*args):
            filtro_canvas.xview_moveto(args[0])
            hsb.set(*args)

        tree = ttk.Treeview(
            table,
            columns=cols,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=_tree_xview
        )
        vsb.config(command=tree.yview)

        def _scroll_x(*args):
            tree.xview(*args)
            filtro_canvas.xview(*args)

        hsb.config(command=_scroll_x)

        # Ubicar el Treeview en row=1, columna 0..3
        tree.grid(row=1, column=0, columnspan=len(cols), sticky='nsew')
        vsb.grid(row=1, column=len(cols), sticky='ns')
        hsb.grid(row=2, column=0, columnspan=len(cols), sticky='ew')
        table.grid_rowconfigure(1, weight=1)

        for c in cols:
            tree.heading(c, text=c, anchor='center')
            tree.column(c, anchor='center', stretch=True)

        # 9) Poblamos inicialmente
        def poblar_tax_cobros(lista):
            for item in tree.get_children():
                tree.delete(item)
            for row in lista:
                cuenta, iibb_pct, dbcr_pct = row
                nombre = self.plan.get(cuenta, '')
                tree.insert('', 'end', values=(cuenta, nombre, iibb_pct, dbcr_pct))

        poblar_tax_cobros(regs)

        # 10) Función de filtrado (solo "Cuenta" y "Nombre")
        def aplicar_filtros_tax_cobros(event=None):
            filtros = {idx: ent.get().strip() for idx, ent in filtro_entrys.items()}
            filtrados = []

            for row in regs:
                cuenta, iibb_pct, dbcr_pct = row
                match = True

                # Filtrar por "Cuenta" (col_idx = 0)
                txt0 = filtros.get(0, "")
                if txt0:
                    if txt0.lower() not in cuenta.lower():
                        match = False

                # Filtrar por "Nombre" (col_idx = 1)
                txt1 = filtros.get(1, "")
                if match and txt1:
                    nombre = self.plan.get(cuenta, '')
                    if txt1.lower() not in nombre.lower():
                        match = False

                if match:
                    filtrados.append(row)

            poblar_tax_cobros(filtrados)

        ent_cuenta.bind('<KeyRelease>', aplicar_filtros_tax_cobros)
        ent_nombre.bind('<KeyRelease>', aplicar_filtros_tax_cobros)

        # 11) Botón “Eliminar seleccionado” (row=3)
        btn_frame = ttk.Frame(cont)
        btn_frame.grid(row=1, column=0, sticky='w', pady=(5,0))
        boton_elim = ttk.Button(btn_frame, text='Eliminar seleccionado', style='Big.TButton')
        boton_elim.grid(row=0, column=0, padx=5)
        boton_edit = ttk.Button(btn_frame, text='Editar seleccionado', style='Big.TButton')
        boton_edit.grid(row=0, column=1, padx=5)

        def eliminar_tax_cobros():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione un registro.')
                return
            vals = tree.item(sel[0], 'values')
            num_cuenta = vals[0]
            if not messagebox.askyesno('Confirmar', f'¿Eliminar impuestos para cuenta {num_cuenta}?'):
                return

            originales = []
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    tup = ast.literal_eval(line)
                    if str(tup[0]) == str(num_cuenta):
                        continue
                    originales.append(tup)
            overwrite_records(full_path, originales)

            nonlocal regs
            regs = [(str(r[0]), float(r[1]), float(r[2])) for r in originales]
            aplicar_filtros_tax_cobros()

        boton_elim.config(command=eliminar_tax_cobros)

        def editar_tax_cobros():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione un registro.')
                return
            vals = tree.item(sel[0], 'values')
            num_cuenta = vals[0]
            idx_reg = None
            for i, r in enumerate(regs):
                if str(r[0]) == str(num_cuenta):
                    idx_reg = i
                    break
            if idx_reg is None:
                return

            orig_row = list(regs[idx_reg])

            win = tk.Toplevel(self)
            win.title('Editar impuestos')
            ttk.Label(win, text='Cuenta:', style='Field.TLabel').grid(row=0, column=0, sticky='e', padx=5, pady=2)
            e_c = ttk.Entry(win, style='Field.TEntry')
            e_c.grid(row=0, column=1, padx=5, pady=2)
            e_c.insert(0, vals[0])
            ttk.Label(win, text='%IIBB:', style='Field.TLabel').grid(row=1, column=0, sticky='e', padx=5, pady=2)
            e_i = ttk.Entry(win, style='Field.TEntry')
            e_i.grid(row=1, column=1, padx=5, pady=2)
            e_i.insert(0, vals[2])
            ttk.Label(win, text='%DByCR:', style='Field.TLabel').grid(row=2, column=0, sticky='e', padx=5, pady=2)
            e_d = ttk.Entry(win, style='Field.TEntry')
            e_d.grid(row=2, column=1, padx=5, pady=2)
            e_d.insert(0, vals[3])

            def guardar():
                try:
                    regs[idx_reg] = (e_c.get(), float(e_i.get()), float(e_d.get()))
                    overwrite_records(full_path, regs)
                    aplicar_filtros_tax_cobros()
                    win.destroy()
                except ValueError:
                    messagebox.showerror('Error', 'Valores inválidos')

            ttk.Button(win, text='Guardar', command=guardar, style='Big.TButton').grid(row=3, column=0, columnspan=2, pady=10)

        boton_edit.config(command=editar_tax_cobros)

        # 12) Formulario “Agregar” (row=4)
        f2 = ttk.Frame(cont, padding=5)
        f2.grid(row=2, column=0, sticky='ew', padx=10, pady=10)
        ttk.Label(f2, text='Cuenta:', style='Field.TLabel').grid(row=0, column=0)
        e_c = ttk.Entry(f2, style='Field.TEntry'); e_c.grid(row=0, column=1)
        ttk.Label(f2, text='%IIBB:').grid(row=0, column=2, padx=10)
        e_i = ttk.Entry(f2, style='Field.TEntry'); e_i.grid(row=0, column=3)
        ttk.Label(f2, text='%DByCR:').grid(row=0, column=4, padx=10)
        e_d = ttk.Entry(f2, style='Field.TEntry'); e_d.grid(row=0, column=5)
        ttk.Button(
            f2,
            text='Agregar',
            style='Big.TButton',
            command=lambda: (
                save_tax_cobros(((e_c.get(), float(e_i.get()), float(e_d.get())),)),
                messagebox.showinfo('Éxito', 'Registro Cobros agregado.'),
                self._show_frame('tax_cobros')
            )
        ).grid(row=1, column=0, columnspan=6, pady=10)

    def _build_tax_pagos(self, parent):
        # 0) Limpiar todo
        for w in parent.winfo_children():
            w.destroy()

        lbl_title = ttk.Label(parent, text='Tabla Impositiva - Pagos', style='Title.TLabel')
        lbl_title.pack(pady=10)

        full_path = os.path.join(ensure_data_directory(), 'tax_pagos.txt')
        tbl = load_tax_pagos()  # dict { 'cuenta': pct_dbcr }
        regs = [(num, tbl[num]) for num in tbl]
        # regs = [(cuenta, pct_dbcr), ...]

        cont = ttk.Frame(parent, padding=10)
        cont.pack(expand=True, fill='both')

        cols = ['Cuenta', 'Nombre', '%DByCR Banc.']

        # PREPARAMOS GRID COLUMNS = 3
        cont.grid_columnconfigure(0, weight=1)

        table = ttk.Frame(cont)
        table.grid(row=0, column=0, sticky='nsew')
        cont.grid_rowconfigure(0, weight=1)

        filtro_canvas = tk.Canvas(table, highlightthickness=0)
        filtro_canvas.grid(row=0, column=0, columnspan=len(cols), sticky='ew')
        filtro_canvas.configure(xscrollcommand=lambda *a: hsb.set(*a))

        filtro_frame = ttk.Frame(filtro_canvas)
        filtro_canvas.create_window((0, 0), window=filtro_frame, anchor='nw')

        # — FILTROS (row=0) — solo para las primeras dos
        filtro_entrys = {}
        ent_cuenta = PlaceholderEntry(filtro_frame, placeholder='Cuenta', style='Field.TEntry')
        ent_cuenta.grid(row=0, column=0, padx=1, pady=(0,5), sticky='ew')
        filtro_frame.grid_columnconfigure(0, weight=1)
        filtro_entrys[0] = ent_cuenta

        ent_nombre = PlaceholderEntry(filtro_frame, placeholder='Nombre', style='Field.TEntry')
        ent_nombre.grid(row=0, column=1, padx=1, pady=(0,5), sticky='ew')
        filtro_frame.grid_columnconfigure(1, weight=1)
        filtro_entrys[1] = ent_nombre

        # Reservamos columna 2 (%DByCR Banc.) solo como espacio en blanco
        ttk.Label(filtro_frame, text='').grid(row=0, column=2, padx=1, pady=(0,5))

        filtro_canvas.update_idletasks()
        filtro_canvas.configure(scrollregion=filtro_canvas.bbox('all'))

        vsb = ttk.Scrollbar(table, orient='vertical')
        hsb = ttk.Scrollbar(table, orient='horizontal')

        def _tree_xview(*args):
            filtro_canvas.xview_moveto(args[0])
            hsb.set(*args)

        tree = ttk.Treeview(
            table,
            columns=cols,
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=_tree_xview
        )
        vsb.config(command=tree.yview)

        def _scroll_x(*args):
            tree.xview(*args)
            filtro_canvas.xview(*args)

        hsb.config(command=_scroll_x)

        # Ubicar el Treeview en row=1, columna 0..2
        tree.grid(row=1, column=0, columnspan=len(cols), sticky='nsew')
        vsb.grid(row=1, column=len(cols), sticky='ns')
        hsb.grid(row=2, column=0, columnspan=len(cols), sticky='ew')

        table.grid_rowconfigure(1, weight=1)

        for c in cols:
            tree.heading(c, text=c, anchor='center')
            tree.column(c, width=140, anchor='center')

        # 3) Poblamos inicialmente
        def poblar_tax_pagos(lista):
            for item in tree.get_children():
                tree.delete(item)
            for row in lista:
                cuenta, pct_dbcr = row
                nombre = self.plan.get(cuenta, '')
                tree.insert('', 'end', values=(cuenta, nombre, pct_dbcr))

        poblar_tax_pagos(regs)

        # 4) Función de filtrado (solo “Cuenta” y “Nombre”)
        def aplicar_filtros_tax_pagos(event=None):
            filtros = {idx: ent.get().strip() for idx, ent in filtro_entrys.items()}
            filtrados = []

            for row in regs:
                cuenta, pct_dbcr = row
                match = True

                # Filtro "Cuenta" (col_idx = 0)
                txt0 = filtros.get(0, "")
                if txt0:
                    if txt0.lower() not in cuenta.lower():
                        match = False

                # Filtro "Nombre" (col_idx = 1)
                txt1 = filtros.get(1, "")
                if match and txt1:
                    nombre = self.plan.get(cuenta, '')
                    if txt1.lower() not in nombre.lower():
                        match = False

                if match:
                    filtrados.append(row)

            poblar_tax_pagos(filtrados)

        ent_cuenta.bind('<KeyRelease>', aplicar_filtros_tax_pagos)
        ent_nombre.bind('<KeyRelease>', aplicar_filtros_tax_pagos)

        # 5) Botón “Eliminar seleccionado” (row=3)
        btn_frame = ttk.Frame(cont)
        btn_frame.grid(row=1, column=0, sticky='w', pady=(10,0))
        boton_elim = ttk.Button(btn_frame, text='Eliminar seleccionado', style='Big.TButton')
        boton_elim.grid(row=0, column=0, padx=5)
        boton_edit = ttk.Button(btn_frame, text='Editar seleccionado', style='Big.TButton')
        boton_edit.grid(row=0, column=1, padx=5)

        def eliminar_tax_pagos():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione un registro.')
                return
            vals = tree.item(sel[0], 'values')
            num_cuenta = vals[0]
            if not messagebox.askyesno('Confirmar', f'¿Eliminar impuestos para cuenta {num_cuenta}?'):
                return

            originales = []
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    tup = ast.literal_eval(line)
                    if str(tup[0]) == str(num_cuenta):
                        continue
                    originales.append(tup)
            overwrite_records(full_path, originales)

            nonlocal regs
            regs = [(str(r[0]), float(r[1])) for r in originales]
            aplicar_filtros_tax_pagos()

        boton_elim.config(command=eliminar_tax_pagos)

        def editar_tax_pagos():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning('Atención', 'Seleccione un registro.')
                return
            vals = tree.item(sel[0], 'values')
            num_cuenta = vals[0]
            idx_reg = None
            for i, r in enumerate(regs):
                if str(r[0]) == str(num_cuenta):
                    idx_reg = i
                    break
            if idx_reg is None:
                return

            win = tk.Toplevel(self)
            win.title('Editar impuesto')
            ttk.Label(win, text='Cuenta:', style='Field.TLabel').grid(row=0, column=0, sticky='e', padx=5, pady=2)
            e_c = ttk.Entry(win, style='Field.TEntry')
            e_c.grid(row=0, column=1, padx=5, pady=2)
            e_c.insert(0, vals[0])
            ttk.Label(win, text='%DByCR Banc.:', style='Field.TLabel').grid(row=1, column=0, sticky='e', padx=5, pady=2)
            e_d = ttk.Entry(win, style='Field.TEntry')
            e_d.grid(row=1, column=1, padx=5, pady=2)
            e_d.insert(0, vals[2])

            def guardar():
                try:
                    regs[idx_reg] = (e_c.get(), float(e_d.get()))
                    overwrite_records(full_path, regs)
                    aplicar_filtros_tax_pagos()
                    win.destroy()
                except ValueError:
                    messagebox.showerror('Error', 'Valores inválidos')

            ttk.Button(win, text='Guardar', command=guardar, style='Big.TButton').grid(row=2, column=0, columnspan=2, pady=10)

        boton_edit.config(command=editar_tax_pagos)

        # 6) Formulario para agregar nuevo registro (row=4)
        f2 = ttk.Frame(cont, padding=5)
        f2.grid(row=2, column=0, sticky='ew', pady=(10,0))
        ttk.Label(f2, text='Cuenta:', style='Field.TLabel').grid(row=0, column=0)
        e_c = ttk.Entry(f2, style='Field.TEntry'); e_c.grid(row=0, column=1, padx=(5,20))
        ttk.Label(f2, text='%DByCR Banc.:').grid(row=0, column=2)
        e_d = ttk.Entry(f2, style='Field.TEntry'); e_d.grid(row=0, column=3, padx=(5,0))
        ttk.Button(
            f2,
            text='Agregar',
            style='Big.TButton',
            command=lambda: (
                save_tax_pagos(((e_c.get(), float(e_d.get())),)),
                messagebox.showinfo('Éxito', 'Registro Pagos agregado.'),
                self._show_frame('tax_pagos')
            )
        ).grid(row=1, column=0, columnspan=4, pady=(10,0))

if __name__ == '__main__':
    App().mainloop()
