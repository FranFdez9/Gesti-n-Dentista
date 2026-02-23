
# Importamos tkinter para crear ventanas y botones
import tkinter as tk
# ttk son widgets más modernos de tkinter, messagebox para ventanas emergentes
from tkinter import ttk, messagebox
# PIL para manejar imágenes (cargar y redimensionar)
from PIL import Image, ImageTk
# datetime para trabajar con fechas y horas
from datetime import datetime
# sqlite3 para la base de datos
import sqlite3
# os para operaciones del sistema (abrir archivos)
import os
# reportlab para generar PDFs profesionales
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
# re para expresiones regulares (validar email)
import re

# Definimos el tamaño de las ventanas: 1920x1080 (Full HD)
ANCHO = 1920
ALTO = 1080
# Nombre del archivo de base de datos
DB = "clinica.db"


# =====================================================
# FUNCIONES DE VALIDACIÓN (OPTIMIZADAS)
# =====================================================

def validar_email(email):
    """Valida que el email tenga formato correcto - VERSIÓN OPTIMIZADA"""
    # Patrón simplificado y más rápido
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    # Comprobamos si el email coincide con el patrón
    return re.match(patron, email) is not None


def validar_telefono(telefono):
    """Valida que el teléfono solo tenga números y espacios"""
    # Permitimos números, espacios, guiones y paréntesis
    # Quitamos todos los caracteres permitidos y verificamos que solo queden números
    limpio = telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return limpio.isdigit() and len(limpio) >= 9


def validar_numero_positivo(texto):
    """Valida que sea un número positivo"""
    try:
        # Intentamos convertir a número
        num = float(texto)
        # Verificamos que sea mayor que 0
        return num > 0
    except:
        # Si no se puede convertir, devolvemos False
        return False


def validar_no_vacio(texto):
    """Valida que el campo no esté vacío"""
    # strip() quita espacios al inicio y final
    return texto.strip() != ""


# =====================================================
# BASE DE DATOS (CON ÍNDICES PARA MEJOR RENDIMIENTO)
# =====================================================

def crear_bd():
    """Esta función crea las tablas de la base de datos si no existen"""
    # Conectamos con la base de datos (la crea si no existe)
    conn = sqlite3.connect(DB)
    # Creamos un cursor para ejecutar comandos SQL
    cur = conn.cursor()

    # Creamos tabla de clientes con 5 campos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único que se incrementa solo
        nombre TEXT,                            -- Nombre del cliente
        apellidos TEXT,                         -- Apellidos del cliente
        telefono TEXT,                          -- Teléfono del cliente
        email TEXT                              -- Email del cliente
    )
    """)

    # Creamos tabla de dentistas con 5 campos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dentistas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único
        nombre TEXT,                            -- Nombre del dentista
        apellidos TEXT,                         -- Apellidos del dentista
        especialidad TEXT,                      -- Especialidad (General, Ortodoncia, etc)
        activo INTEGER                          -- 1=activo, 0=inactivo
    )
    """)

    # Creamos tabla de citas con 7 campos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único de la cita
        id_cliente INTEGER,                     -- Referencia al cliente
        id_dentista INTEGER,                    -- Referencia al dentista
        fecha TEXT,                             -- Fecha de la cita (formato texto)
        hora TEXT,                              -- Hora de la cita (formato texto)
        motivo TEXT,                            -- Motivo de la cita
        estado TEXT                             -- Estado: Pendiente, Realizada, Cancelada
    )
    """)

    # Creamos tabla de facturas con 7 campos
    cur.execute("""
   CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,      -- ID único de la factura
    id_cita INTEGER NOT NULL,                   -- Referencia a la cita (obligatorio)
    id_cliente INTEGER NOT NULL,                -- Referencia al cliente (obligatorio)
    fecha TEXT NOT NULL,                        -- Fecha de la factura (obligatorio)
    concepto TEXT NOT NULL,                     -- Descripción del servicio (obligatorio)
    importe REAL NOT NULL,                      -- Precio en euros (obligatorio)
    pagada INTEGER NOT NULL DEFAULT 0,          -- 0=no pagada, 1=pagada (por defecto 0)

    FOREIGN KEY (id_cita) REFERENCES citas(id),     -- Relación con tabla citas
    FOREIGN KEY (id_cliente) REFERENCES clientes(id) -- Relación con tabla clientes
    )
    """)

    # ✅ OPTIMIZACIÓN: Crear índices para búsquedas más rápidas
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_citas_fecha ON citas(fecha)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_citas_cliente ON citas(id_cliente)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_citas_dentista ON citas(id_dentista)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(id_cliente)")

    # Guardamos los cambios en la base de datos
    conn.commit()
    # Cerramos la conexión
    conn.close()


# =====================================================
# UTILIDADES UI (Interfaz de Usuario)
# =====================================================

def editar_registro(tabla, nombre_tabla, columnas):
    """Función para editar cualquier registro de cualquier tabla haciendo doble clic"""
    # Obtenemos el elemento seleccionado en la tabla
    sel = tabla.selection()
    # Si no hay nada seleccionado, salimos
    if not sel:
        return

    # Obtenemos los valores de la fila seleccionada
    valores = tabla.item(sel[0])["values"]
    # El primer valor siempre es el ID
    id_registro = valores[0]

    # Creamos una ventana nueva encima de la actual
    win = tk.Toplevel()
    win.title("Editar registro")
    win.geometry("400x350")  # Tamaño de la ventana
    win.grab_set()  # Hace que esta ventana sea modal (bloquea la anterior)

    # Creamos un marco con espaciado de 20 píxeles
    cont = ttk.Frame(win, padding=20)
    cont.pack(expand=True)  # Lo expandimos para llenar la ventana

    # Lista para guardar los campos de entrada
    entradas = []

    # Crear campos editables (menos ID porque no se edita)
    for i, col in enumerate(columnas):
        # Creamos una etiqueta con el nombre del campo
        ttk.Label(cont, text=col).grid(row=i, column=0, pady=10)

        # Creamos un campo de entrada
        e = ttk.Entry(cont)
        # Insertamos el valor actual (saltamos el ID por eso +1)
        e.insert(0, valores[i + 1])
        # Lo colocamos en la cuadrícula
        e.grid(row=i, column=1)

        # Guardamos el campo en la lista
        entradas.append(e)

    def guardar():
        """Función interna que guarda los cambios en la base de datos"""
        # Conectamos con la base de datos
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Construye dinámicamente el UPDATE (nombre=?, apellidos=?, etc)
        campos_sql = ", ".join([f"{c}=?" for c in columnas])

        # Ejecutamos el UPDATE con los nuevos valores
        cur.execute(
            f"UPDATE {nombre_tabla} SET {campos_sql} WHERE id=?",
            [e.get() for e in entradas] + [id_registro]  # Valores + ID al final
        )

        # Guardamos cambios
        conn.commit()
        conn.close()

        # Cerramos la ventana de edición
        win.destroy()

    # Botón para guardar los cambios
    ttk.Button(cont, text="Guardar cambios", command=guardar) \
        .grid(row=len(columnas), columnspan=2, pady=15)


def centrar(v):
    """Centra una ventana en medio de la pantalla"""
    # Actualiza la ventana para obtener dimensiones reales
    v.update_idletasks()
    # Calcula la posición X para centrar
    x = (v.winfo_screenwidth() // 2) - (ANCHO // 2)
    # Calcula la posición Y para centrar
    y = (v.winfo_screenheight() // 2) - (ALTO // 2)
    # Aplica el tamaño y posición
    v.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")


def fondo(v, ruta):
    """Pone una imagen de fondo en una ventana"""
    # Abre la imagen y la redimensiona al tamaño de la ventana
    img = Image.open(ruta).resize((ANCHO, ALTO))
    # Convierte la imagen a formato que tkinter puede usar
    f = ImageTk.PhotoImage(img)
    # Guardamos referencia para que no se borre de memoria
    v.fondo = f

    # Creamos un lienzo (canvas) donde dibujar
    canvas = tk.Canvas(v, width=ANCHO, height=ALTO, highlightthickness=0)
    canvas.pack(fill="both", expand=True)  # Lo expandimos para llenar todo
    # Dibujamos la imagen en posición 0,0 (esquina superior izquierda)
    canvas.create_image(0, 0, image=f, anchor="nw")
    # Devolvemos el canvas para poder añadir cosas encima
    return canvas


# =====================================================
# DASHBOARD CON ESTADÍSTICAS
# =====================================================

def ventana_dashboard(raiz):
    """Ventana que muestra estadísticas generales de la clínica"""
    # Creamos una ventana nueva
    v = tk.Toplevel(raiz)
    v.title("📊 Dashboard")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)  # La centramos

    # Ponemos imagen de fondo
    canvas = fondo(v, "Clínica dental moderna y profesional.png")
    # Creamos un marco para los datos
    frame = ttk.Frame(canvas, padding=40)
    # Lo colocamos en el centro del canvas (960, 540 = mitad de 1920x1080)
    canvas.create_window(960, 540, window=frame)

    # Conectamos a la base de datos
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Contamos cuántos clientes hay en total
    cur.execute("SELECT COUNT(*) FROM clientes")
    clientes = cur.fetchone()[0]  # fetchone devuelve una tupla, tomamos el primer valor

    # Contamos citas de hoy
    cur.execute("SELECT COUNT(*) FROM citas WHERE fecha=?", (datetime.now().strftime("%d/%m/%Y"),))
    citas_hoy = cur.fetchone()[0]

    # Sumamos todos los importes de las facturas (si no hay, devuelve 0)
    cur.execute("SELECT IFNULL(SUM(importe),0) FROM facturas")
    ingresos = cur.fetchone()[0]

    # Cerramos conexión
    conn.close()

    # Lista con los datos a mostrar (texto, número)
    datos = [
        ("👥 Clientes totales", clientes),
        ("📅 Citas hoy", citas_hoy),
        ("💰 Ingresos totales €", ingresos),
    ]

    # Para cada dato, creamos una etiqueta grande y la mostramos
    for i, (txt, num) in enumerate(datos):
        ttk.Label(frame, text=f"{txt}: {num}", font=("Segoe UI", 28, "bold")).grid(row=i, column=0, pady=20)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=3, column=0, pady=30)


# =====================================================
# CLIENTES CRUD + EDICIÓN DIRECTA + BÚSQUEDA (OPTIMIZADO)
# =====================================================

def ventana_clientes(raiz):
    """Ventana para gestionar clientes con búsqueda y validaciones - OPTIMIZADA"""
    # Creamos ventana nueva
    v = tk.Toplevel(raiz)
    v.title("👥 Clientes")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    # Ponemos fondo
    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=30)
    canvas.create_window(960, 540, window=frame)

    # ========== BARRA DE BÚSQUEDA ==========
    # Frame superior para búsqueda
    frame_busqueda = ttk.Frame(frame)
    frame_busqueda.grid(row=0, column=0, columnspan=3, pady=10)

    ttk.Label(frame_busqueda, text="🔍 Buscar:", font=("Segoe UI", 12)).pack(side="left", padx=5)
    # Campo de entrada para búsqueda
    entrada_busqueda = ttk.Entry(frame_busqueda, width=30)
    entrada_busqueda.pack(side="left", padx=5)

    # ========== TABLA ==========
    # Definimos las columnas de la tabla
    cols = ("ID", "Nombre", "Apellidos", "Teléfono", "Email")
    # Creamos una tabla (Treeview) con esas columnas, altura de 18 filas
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=18)

    # Configuramos cada columna: encabezado y ancho
    for c in cols:
        tabla.heading(c, text=c)  # Texto del encabezado
        tabla.column(c, width=180, anchor="center")  # Ancho y centrado

    # Cambiamos la fila de la tabla porque ahora tenemos búsqueda arriba
    tabla.grid(row=1, column=0, columnspan=3, pady=20)

    # ---------- Edición al hacer doble clic ----------
    # Cuando haces doble clic en una fila, se abre ventana de edición
    tabla.bind("<Double-1>", lambda e: editar_registro(
        tabla,
        "clientes",  # Nombre de la tabla en la BD
        ["nombre", "apellidos", "telefono", "email"]  # Campos editables
    ))

    # ========== REFRESCAR CON BÚSQUEDA ==========
    def refrescar(filtro=""):
        """Recarga clientes, opcionalmente filtrados por búsqueda"""
        # Limpiamos tabla SIEMPRE primero
        for i in tabla.get_children():
            tabla.delete(i)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Si hay filtro, buscamos
        if filtro.strip():  # Verificamos que no esté vacío
            query = """
            SELECT * FROM clientes 
            WHERE nombre LIKE ? 
            OR apellidos LIKE ? 
            OR telefono LIKE ? 
            OR email LIKE ?
            """
            # El % significa "cualquier cosa antes y después"
            patron = f"%{filtro}%"
            resultados = cur.execute(query, (patron, patron, patron, patron))

            # Contamos resultados
            filas = resultados.fetchall()

            # Si no hay resultados, mostramos mensaje
            if not filas:
                conn.close()
                messagebox.showinfo("🔍 Sin resultados", f"No se encontraron clientes con '{filtro}'", parent=v)
                return

            # Insertamos los resultados
            for fila in filas:
                tabla.insert("", "end", values=fila)
        else:
            # Sin filtro, mostramos todos
            for fila in cur.execute("SELECT * FROM clientes"):
                tabla.insert("", "end", values=fila)

        conn.close()

    # ========== FUNCIÓN DE BÚSQUEDA MEJORADA ==========
    def buscar():
        """Ejecuta la búsqueda cuando se escribe en el campo"""
        filtro = entrada_busqueda.get().strip()  # Quitamos espacios

        if not filtro:  # Si está vacío
            messagebox.showwarning("⚠️ Aviso", "Escribe algo para buscar", parent=v)
            return

        refrescar(filtro)

    # ========== FUNCIÓN PARA LIMPIAR BÚSQUEDA ==========
    def limpiar_busqueda():
        """Limpia el campo y muestra todos los clientes"""
        entrada_busqueda.delete(0, tk.END)  # Borra el texto del campo
        refrescar()  # Muestra todos sin filtro

    # BOTONES DE BÚSQUEDA
    ttk.Button(frame_busqueda, text="🔍 Buscar", command=buscar).pack(side="left", padx=5)
    ttk.Button(frame_busqueda, text="🧹 Limpiar", command=limpiar_busqueda).pack(side="left", padx=5)

    # Búsqueda automática al presionar Enter
    entrada_busqueda.bind("<Return>", lambda e: buscar())

    # ========== NUEVO CON VALIDACIONES (OPTIMIZADO) ==========
    def nuevo():
        """Ventana para crear cliente con validaciones - OPTIMIZADA"""
        win = tk.Toplevel(v)
        win.title("Nuevo cliente")
        win.geometry("400x350")
        win.transient(v)  # Esta SÍ es modal porque es una ventana emergente pequeña
        win.grab_set()

        cont = ttk.Frame(win, padding=20)
        cont.pack(expand=True)

        labels = ["Nombre*", "Apellidos*", "Teléfono*", "Email*"]
        entradas = []

        for i, txt in enumerate(labels):
            ttk.Label(cont, text=txt).grid(row=i, column=0, pady=10, sticky="w")
            e = ttk.Entry(cont, width=25)
            e.grid(row=i, column=1, pady=10)
            entradas.append(e)

        # Label para mostrar errores
        label_error = ttk.Label(cont, text="", foreground="red")
        label_error.grid(row=4, column=0, columnspan=2, pady=5)

        def guardar():
            """Guarda con validaciones - VERSIÓN OPTIMIZADA"""
            # Obtenemos los valores
            nombre = entradas[0].get()
            apellidos = entradas[1].get()
            telefono = entradas[2].get()
            email = entradas[3].get()

            # ===== VALIDACIONES =====
            # 1. Campos no vacíos
            if not validar_no_vacio(nombre):
                label_error.config(text="❌ El nombre no puede estar vacío")
                return

            if not validar_no_vacio(apellidos):
                label_error.config(text="❌ Los apellidos no pueden estar vacíos")
                return

            # 2. Teléfono válido
            if not validar_telefono(telefono):
                label_error.config(text="❌ Teléfono inválido (mínimo 9 dígitos)")
                return

            # 3. Email válido
            if not validar_email(email):
                label_error.config(text="❌ Email inválido (formato: ejemplo@correo.com)")
                return

            # Si pasa todas las validaciones, guardamos
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO clientes(nombre,apellidos,telefono,email) VALUES (?,?,?,?)",
                (nombre, apellidos, telefono, email)
            )

            # ✅ OPTIMIZACIÓN: Obtenemos el ID del nuevo registro
            nuevo_id = cur.lastrowid

            conn.commit()
            conn.close()

            # ✅ OPTIMIZACIÓN: Añadimos solo la nueva fila sin refrescar todo
            tabla.insert("", "end", values=(nuevo_id, nombre, apellidos, telefono, email))

            win.destroy()
            messagebox.showinfo("✅ Éxito", "Cliente creado correctamente", parent=v)

        ttk.Button(cont, text="💾 Guardar", command=guardar).grid(row=5, columnspan=2, pady=10)

    # ========== ELIMINAR CON CONFIRMACIÓN ==========
    def eliminar():
        """Elimina con confirmación"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona un cliente", parent=v)
            return

        # Obtenemos datos del cliente
        valores = tabla.item(sel[0])["values"]
        nombre_completo = f"{valores[1]} {valores[2]}"

        # Pedimos confirmación
        respuesta = messagebox.askyesno(
            "❓ Confirmar eliminación",
            f"¿Estás seguro de eliminar a {nombre_completo}?\n\n⚠️ Esta acción no se puede deshacer.",
            parent=v
        )

        if respuesta:  # Si dice que sí
            id_sel = valores[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("DELETE FROM clientes WHERE id=?", (id_sel,))
            conn.commit()
            conn.close()

            # ✅ OPTIMIZACIÓN: Solo eliminamos la fila de la tabla visual
            tabla.delete(sel[0])

            messagebox.showinfo("✅ Éxito", "Cliente eliminado correctamente", parent=v)

    # ========== BOTONES PRINCIPALES ==========
    ttk.Button(frame, text="➕ Nuevo", command=nuevo).grid(row=2, column=0, pady=10)
    ttk.Button(frame, text="🗑️ Eliminar", command=eliminar).grid(row=2, column=1, pady=10)
    ttk.Button(frame, text="🔄 Refrescar", command=refrescar).grid(row=2, column=2, pady=10)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=3, column=0, columnspan=3, pady=20)

    # Cargamos los datos al abrir la ventana
    refrescar()


# =====================================================
# DENTISTAS CRUD (OPTIMIZADO)
# =====================================================

def ventana_dentistas(raiz):
    """Ventana para gestionar dentistas - OPTIMIZADA"""
    # Creamos ventana
    v = tk.Toplevel(raiz)
    v.title("👨‍⚕️ Dentistas")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    # Fondo
    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=30)
    canvas.create_window(960, 540, window=frame)

    # Columnas de la tabla
    cols = ("ID", "Nombre", "Apellidos", "Especialidad", "Activo")
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=18)

    for c in cols:
        tabla.heading(c, text=c)
        tabla.column(c, width=180, anchor="center")

    tabla.grid(row=0, column=0, columnspan=3, pady=20)

    # Doble clic para editar
    tabla.bind("<Double-1>", lambda e: editar_registro(
        tabla,
        "dentistas",
        ["nombre", "apellidos", "especialidad", "activo"]
    ))

    def refrescar():
        """Recarga dentistas desde la BD"""
        # Limpiamos tabla
        for i in tabla.get_children():
            tabla.delete(i)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        # Seleccionamos todos los dentistas
        for fila in cur.execute("SELECT * FROM dentistas"):
            # fila[4] es el campo activo (1 o 0), lo convertimos a "Sí" o "No"
            estado = "Sí" if fila[4] else "No"
            # Insertamos en la tabla mostrando Sí/No en lugar de 1/0
            tabla.insert("", "end", values=(fila[0], fila[1], fila[2], fila[3], estado))
        conn.close()

    def nuevo():
        """Ventana para crear nuevo dentista - OPTIMIZADA"""
        win = tk.Toplevel(v)
        win.title("Nuevo dentista")
        win.geometry("400x300")
        win.transient(v)
        win.grab_set()

        cont = ttk.Frame(win, padding=20)
        cont.pack(expand=True)

        # Campo nombre
        ttk.Label(cont, text="Nombre*").grid(row=0, column=0, pady=10)
        e_nombre = ttk.Entry(cont)
        e_nombre.grid(row=0, column=1)

        # Campo apellidos
        ttk.Label(cont, text="Apellidos*").grid(row=1, column=0, pady=10)
        e_apellidos = ttk.Entry(cont)
        e_apellidos.grid(row=1, column=1)

        # Campo especialidad (desplegable con 3 opciones)
        ttk.Label(cont, text="Especialidad").grid(row=2, column=0, pady=10)
        combo = ttk.Combobox(cont, values=["General", "Ortodoncia", "Implantes"], state="readonly")
        combo.grid(row=2, column=1)
        combo.current(0)  # Seleccionamos la primera opción por defecto

        # Checkbox para activo (por defecto marcado = 1)
        activo_var = tk.IntVar(value=1)
        ttk.Checkbutton(cont, text="Activo", variable=activo_var).grid(row=3, columnspan=2, pady=10)

        def guardar():
            """Guarda el dentista en la BD - OPTIMIZADO"""
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dentistas(nombre,apellidos,especialidad,activo) VALUES (?,?,?,?)",
                (e_nombre.get(), e_apellidos.get(), combo.get(), activo_var.get())
            )

            # ✅ OPTIMIZACIÓN: Obtener ID del nuevo registro
            nuevo_id = cur.lastrowid

            conn.commit()
            conn.close()

            # ✅ OPTIMIZACIÓN: Añadir solo la nueva fila
            estado = "Sí" if activo_var.get() else "No"
            tabla.insert("", "end", values=(nuevo_id, e_nombre.get(), e_apellidos.get(), combo.get(), estado))

            win.destroy()

        ttk.Button(cont, text="💾 Guardar", command=guardar).grid(row=4, columnspan=2, pady=10)

    def eliminar():
        """Elimina dentista seleccionado"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona un dentista", parent=v)
            return

        id_sel = tabla.item(sel[0])["values"][0]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM dentistas WHERE id=?", (id_sel,))
        conn.commit()
        conn.close()

        # ✅ OPTIMIZACIÓN: Solo eliminar de la tabla visual
        tabla.delete(sel[0])

    # Botones
    ttk.Button(frame, text="➕ Nuevo", command=nuevo).grid(row=1, column=0)
    ttk.Button(frame, text="🗑️ Eliminar", command=eliminar).grid(row=1, column=1)
    ttk.Button(frame, text="🔄 Refrescar", command=refrescar).grid(row=1, column=2)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=2, column=0, columnspan=3, pady=15)

    refrescar()


# =====================================================
# MATERIALES CRUD (OPTIMIZADO)
# =====================================================

def ventana_materiales(raiz):
    """Ventana para gestionar materiales (stock de la clínica) - OPTIMIZADA"""
    v = tk.Toplevel(raiz)
    v.title("🦷 Materiales")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=30)
    canvas.create_window(960, 540, window=frame)

    # Primero creamos la tabla en la BD si no existe
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS materiales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único
            nombre TEXT,                            -- Nombre del material
            stock INTEGER,                          -- Cantidad disponible
            precio REAL                             -- Precio unitario
        )
    """)
    conn.commit()
    conn.close()

    # Columnas de la tabla visual
    cols = ("ID", "Nombre", "Stock", "Precio")
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=18)

    for c in cols:
        tabla.heading(c, text=c)
        tabla.column(c, width=180, anchor="center")

    tabla.grid(row=0, column=0, columnspan=3, pady=20)

    # Doble clic para editar
    tabla.bind("<Double-1>", lambda e: editar_registro(
        tabla,
        "materiales",
        ["nombre", "stock", "precio"]
    ))

    def refrescar():
        """Recarga materiales"""
        for i in tabla.get_children():
            tabla.delete(i)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        for fila in cur.execute("SELECT * FROM materiales"):
            tabla.insert("", "end", values=fila)
        conn.close()

    def nuevo():
        """Crear nuevo material - OPTIMIZADO"""
        win = tk.Toplevel(v)
        win.title("Nuevo material")
        win.geometry("300x250")
        win.transient(v)
        win.grab_set()

        cont = ttk.Frame(win, padding=20)
        cont.pack(expand=True)

        entradas = []
        # Creamos 3 campos: Nombre, Stock, Precio
        for i, txt in enumerate(["Nombre", "Stock", "Precio"]):
            ttk.Label(cont, text=txt).grid(row=i, column=0, pady=10)
            e = ttk.Entry(cont)
            e.grid(row=i, column=1)
            entradas.append(e)

        def guardar():
            """Guarda el material - OPTIMIZADO"""
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO materiales(nombre,stock,precio) VALUES (?,?,?)",
                [e.get() for e in entradas]
            )

            # ✅ OPTIMIZACIÓN: Obtener ID y añadir solo nueva fila
            nuevo_id = cur.lastrowid

            conn.commit()
            conn.close()

            # ✅ OPTIMIZACIÓN: Insertar solo la nueva fila
            tabla.insert("", "end", values=(nuevo_id, entradas[0].get(), entradas[1].get(), entradas[2].get()))

            win.destroy()

        ttk.Button(cont, text="💾 Guardar", command=guardar).grid(row=4, columnspan=2, pady=10)

    # Botones
    ttk.Button(frame, text="➕ Nuevo", command=nuevo).grid(row=1, column=0)
    ttk.Button(frame, text="🔄 Refrescar", command=refrescar).grid(row=1, column=1)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=2, column=0, columnspan=3, pady=15)

    refrescar()


# =====================================================
# CITAS PRO + RELACIONES REALES + FILTROS + VALIDACIONES (OPTIMIZADO)
# =====================================================

def ventana_citas(raiz):
    """Ventana para gestionar citas con filtros por fecha y estado - OPTIMIZADA"""
    v = tk.Toplevel(raiz)
    v.title("📅 Citas")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=20)
    canvas.create_window(960, 540, window=frame)

    # ========== BARRA DE FILTROS ==========
    frame_filtros = ttk.Frame(frame)
    frame_filtros.grid(row=0, column=0, columnspan=5, pady=10)

    ttk.Label(frame_filtros, text="📆 Filtrar por fecha:", font=("Segoe UI", 10)).pack(side="left", padx=5)
    # Campo para filtrar por fecha
    entrada_fecha = ttk.Entry(frame_filtros, width=12)
    entrada_fecha.pack(side="left", padx=5)
    entrada_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))  # Fecha de hoy por defecto

    ttk.Label(frame_filtros, text="Estado:", font=("Segoe UI", 10)).pack(side="left", padx=5)
    # Desplegable para filtrar por estado
    combo_estado = ttk.Combobox(
        frame_filtros,
        values=["Todas", "Pendiente", "Realizada", "Cancelada"],
        state="readonly",
        width=12
    )
    combo_estado.pack(side="left", padx=5)
    combo_estado.current(0)  # "Todas" por defecto

    # ========== TABLA ==========
    cols = ("ID", "Cliente", "Dentista", "Fecha", "Hora", "Estado")
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=16)

    for c in cols:
        tabla.heading(c, text=c)
        tabla.column(c, width=150, anchor="center")

    tabla.grid(row=1, column=0, columnspan=5, pady=20)

    # Doble clic para editar
    tabla.bind("<Double-1>", lambda e: editar_registro(
        tabla,
        "citas",
        ["id_cliente", "id_dentista", "fecha", "hora", "motivo", "estado"]
    ))

    # ========== REFRESCAR CON FILTROS ==========
    def refrescar():
        """Recarga citas aplicando filtros"""
        # Limpiamos tabla
        for i in tabla.get_children():
            tabla.delete(i)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Query base con JOIN
        query = """
        SELECT citas.id,
               clientes.nombre || ' ' || clientes.apellidos,
               dentistas.nombre || ' ' || dentistas.apellidos,
               citas.fecha, citas.hora, citas.estado
        FROM citas
        JOIN clientes ON clientes.id = citas.id_cliente
        JOIN dentistas ON dentistas.id = citas.id_dentista
        WHERE 1=1
        """

        parametros = []

        # Filtro por fecha
        fecha_filtro = entrada_fecha.get().strip()
        if fecha_filtro:
            query += " AND citas.fecha = ?"
            parametros.append(fecha_filtro)

        # Filtro por estado
        estado_filtro = combo_estado.get()
        if estado_filtro != "Todas":
            query += " AND citas.estado = ?"
            parametros.append(estado_filtro)

        # Ordenamos por fecha y hora
        query += " ORDER BY citas.fecha, citas.hora"

        # Ejecutamos query
        for fila in cur.execute(query, parametros):
            tabla.insert("", "end", values=fila)

        conn.close()

    # Botón filtrar
    ttk.Button(frame_filtros, text="🔍 Aplicar filtros", command=refrescar).pack(side="left", padx=5)

    # Botón limpiar filtros
    def limpiar_filtros():
        """Limpia los filtros y muestra todas las citas"""
        entrada_fecha.delete(0, tk.END)
        entrada_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))
        combo_estado.current(0)
        refrescar()

    ttk.Button(frame_filtros, text="🧹 Limpiar", command=limpiar_filtros).pack(side="left", padx=5)

    # ========== NUEVA CITA CON VALIDACIONES (OPTIMIZADA) ==========
    def nueva():
        """Ventana para crear cita con validaciones - OPTIMIZADA"""
        win = tk.Toplevel(v)
        win.title("Nueva cita")
        win.geometry("420x450")
        win.transient(v)
        win.grab_set()

        cont = ttk.Frame(win, padding=20)
        cont.pack(expand=True)

        # Obtener clientes y dentistas
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, apellidos FROM clientes")
        clientes = cur.fetchall()

        cur.execute("SELECT id, nombre, apellidos FROM dentistas WHERE activo=1")
        dentistas = cur.fetchall()
        conn.close()

        # Validamos que haya clientes y dentistas
        if not clientes:
            messagebox.showerror("❌ Error", "No hay clientes registrados. Crea un cliente primero.", parent=win)
            win.destroy()
            return

        if not dentistas:
            messagebox.showerror("❌ Error", "No hay dentistas activos. Activa o crea un dentista primero.", parent=win)
            win.destroy()
            return

        # ===== CAMPOS =====
        ttk.Label(cont, text="Cliente*").grid(row=0, column=0, pady=10, sticky="w")
        combo_cliente = ttk.Combobox(
            cont,
            values=[f"{c[0]} - {c[1]} {c[2]}" for c in clientes],
            state="readonly",
            width=25
        )
        combo_cliente.grid(row=0, column=1, pady=10)

        ttk.Label(cont, text="Dentista*").grid(row=1, column=0, pady=10, sticky="w")
        combo_dentista = ttk.Combobox(
            cont,
            values=[f"{d[0]} - {d[1]} {d[2]}" for d in dentistas],
            state="readonly",
            width=25
        )
        combo_dentista.grid(row=1, column=1, pady=10)

        ttk.Label(cont, text="Fecha* (dd/mm/yyyy)").grid(row=2, column=0, pady=10, sticky="w")
        e_fecha = ttk.Entry(cont, width=27)
        e_fecha.grid(row=2, column=1, pady=10)
        # Ponemos fecha de hoy por defecto
        e_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))

        ttk.Label(cont, text="Hora* (hh:mm)").grid(row=3, column=0, pady=10, sticky="w")
        e_hora = ttk.Entry(cont, width=27)
        e_hora.grid(row=3, column=1, pady=10)

        ttk.Label(cont, text="Motivo*").grid(row=4, column=0, pady=10, sticky="w")
        e_motivo = ttk.Entry(cont, width=27)
        e_motivo.grid(row=4, column=1, pady=10)

        # Label para errores
        label_error = ttk.Label(cont, text="", foreground="red", wraplength=350)
        label_error.grid(row=5, column=0, columnspan=2, pady=5)

        def guardar():
            """Guarda cita con validaciones - OPTIMIZADO"""
            # ===== VALIDACIONES =====
            # 1. Campos obligatorios
            if not combo_cliente.get():
                label_error.config(text="❌ Selecciona un cliente")
                return

            if not combo_dentista.get():
                label_error.config(text="❌ Selecciona un dentista")
                return

            if not validar_no_vacio(e_motivo.get()):
                label_error.config(text="❌ El motivo no puede estar vacío")
                return

            # 2. Validar fecha y hora
            try:
                fecha_hora = datetime.strptime(
                    f"{e_fecha.get()} {e_hora.get()}",
                    "%d/%m/%Y %H:%M"
                )

                # No permitir citas en el pasado
                if fecha_hora < datetime.now():
                    label_error.config(text="❌ No puedes crear citas en el pasado")
                    return

            except ValueError:
                label_error.config(text="❌ Fecha u hora incorrecta. Formato: dd/mm/yyyy hh:mm")
                return

            # Si pasa todas las validaciones, guardamos
            id_cliente = int(combo_cliente.get().split("-")[0])
            id_dentista = int(combo_dentista.get().split("-")[0])

            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO citas(id_cliente,id_dentista,fecha,hora,motivo,estado)
                VALUES (?,?,?,?,?,?)
            """, (id_cliente, id_dentista, e_fecha.get(), e_hora.get(), e_motivo.get(), "Pendiente"))

            conn.commit()
            conn.close()

            win.destroy()
            messagebox.showinfo("✅ Éxito", "Cita creada correctamente", parent=v)

            # ✅ OPTIMIZACIÓN: Solo refrescar si los filtros coinciden
            refrescar()

        ttk.Button(cont, text="💾 Guardar cita", command=guardar).grid(row=6, columnspan=2, pady=20)

    # ========== MARCAR REALIZADA ==========
    def marcar_realizada():
        """Marca cita como realizada"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona una cita", parent=v)
            return

        id_cita = tabla.item(sel[0])["values"][0]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("UPDATE citas SET estado='Realizada' WHERE id=?", (id_cita,))
        conn.commit()
        conn.close()

        refrescar()
        messagebox.showinfo("✅ Éxito", "Cita marcada como realizada", parent=v)

    # ========== CANCELAR CITA ==========
    def cancelar_cita():
        """Cancela una cita"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona una cita", parent=v)
            return

        respuesta = messagebox.askyesno("❓ Confirmar", "¿Cancelar esta cita?", parent=v)
        if respuesta:
            id_cita = tabla.item(sel[0])["values"][0]

            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("UPDATE citas SET estado='Cancelada' WHERE id=?", (id_cita,))
            conn.commit()
            conn.close()

            refrescar()
            messagebox.showinfo("✅ Éxito", "Cita cancelada", parent=v)

    # ========== BOTONES ==========
    ttk.Button(frame, text="➕ Nueva cita", command=nueva).grid(row=2, column=0, pady=10)
    ttk.Button(frame, text="✅ Marcar realizada", command=marcar_realizada).grid(row=2, column=1, pady=10)
    ttk.Button(frame, text="❌ Cancelar cita", command=cancelar_cita).grid(row=2, column=2, pady=10)
    ttk.Button(frame, text="🔄 Refrescar", command=refrescar).grid(row=2, column=3, pady=10)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=3, column=0, columnspan=5, pady=15)

    refrescar()


# =====================================================
# PDF FACTURA PROFESIONAL
# =====================================================

def generar_pdf_factura(id_factura):
    """Genera un PDF profesional para una factura"""
    # Conectamos a la BD
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Obtenemos datos de la factura con JOIN para tener el nombre del cliente
    cur.execute("""
    SELECT facturas.id, clientes.nombre, clientes.apellidos,
           facturas.concepto, facturas.importe, facturas.fecha
    FROM facturas
    JOIN clientes ON clientes.id = facturas.id_cliente
    WHERE facturas.id=?
    """, (id_factura,))

    # Guardamos el resultado
    f = cur.fetchone()
    conn.close()

    # Si no existe, salimos
    if not f:
        return

    # Nombre del archivo PDF
    nombre_pdf = f"factura_{id_factura}.pdf"
    # Creamos el documento PDF
    doc = SimpleDocTemplate(nombre_pdf)
    # Obtenemos estilos predefinidos
    styles = getSampleStyleSheet()

    # Lista de elementos a incluir en el PDF
    elementos = []
    # Título
    elementos.append(Paragraph("CLÍNICA DENTAL", styles["Title"]))
    # Espaciado
    elementos.append(Spacer(1, 20))
    # Datos de la factura
    elementos.append(Paragraph(f"Paciente: {f[1]} {f[2]}", styles["Normal"]))
    elementos.append(Paragraph(f"Concepto: {f[3]}", styles["Normal"]))
    elementos.append(Paragraph(f"Importe: {f[4]} €", styles["Normal"]))
    elementos.append(Paragraph(f"Fecha: {f[5]}", styles["Normal"]))

    # Generamos el PDF
    doc.build(elementos)

    # Abrimos el PDF con el programa predeterminado (Windows)
    os.startfile(nombre_pdf)


# =====================================================
# FACTURAS CRUD + PDF
# =====================================================

def ventana_facturas(raiz):
    """Ventana para gestionar facturas"""
    v = tk.Toplevel(raiz)
    v.title("💰 Facturas")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=30)
    canvas.create_window(960, 540, window=frame)

    # Columnas de la tabla
    cols = ("ID", "Cita", "Cliente", "Fecha", "Concepto", "Importe", "Pagada")
    tabla = ttk.Treeview(frame, columns=cols, show="headings", height=18)

    for c in cols:
        tabla.heading(c, text=c)
        tabla.column(c, width=150, anchor="center")

    tabla.grid(row=0, column=0, columnspan=6, pady=20)

    # Doble clic para editar
    tabla.bind("<Double-1>", lambda e: editar_registro(
        tabla,
        "facturas",
        ["id_cita", "id_cliente", "fecha", "concepto", "importe", "pagada"]
    ))

    # =====================================================
    # REFRESCAR TABLA
    # =====================================================
    def refrescar():
        """Recarga todas las facturas"""
        # Limpiamos tabla
        for i in tabla.get_children():
            tabla.delete(i)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Seleccionamos todas las facturas
        query = """
        SELECT id, id_cita, id_cliente, fecha, concepto, importe, pagada
        FROM facturas
        """

        for fila in cur.execute(query):
            # Convertimos 1/0 a Sí/No para mostrar
            estado = "Sí" if fila[6] == 1 else "No"
            tabla.insert("", "end", values=(
                fila[0], fila[1], fila[2], fila[3], fila[4], fila[5], estado
            ))

        conn.close()

    # =====================================================
    # CREAR FACTURA DESDE CITA REALIZADA
    # =====================================================
    def nueva_desde_cita():
        """Crea una factura a partir de una cita realizada"""
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Buscamos citas realizadas que no tengan factura
        cur.execute("""
            SELECT id, id_cliente
            FROM citas
            WHERE estado='Realizada'
            AND id NOT IN (SELECT id_cita FROM facturas)
        """)

        citas = cur.fetchall()

        # Si no hay citas sin facturar
        if not citas:
            messagebox.showinfo("ℹ️ Info", "No hay citas realizadas sin facturar", parent=v)
            conn.close()
            return

        # Ventana para elegir qué cita facturar
        win = tk.Toplevel(v)
        win.title("Seleccionar cita")
        win.geometry("300x200")
        win.transient(v)
        win.grab_set()

        # Desplegable con las citas disponibles
        combo = ttk.Combobox(
            win,
            values=[f"Cita {c[0]} - Cliente {c[1]}" for c in citas],
            state="readonly",
            width=25
        )
        combo.pack(pady=20)
        combo.current(0)

        def crear():
            """Crea la factura para la cita seleccionada"""
            idx = combo.current()
            id_cita, id_cliente = citas[idx]

            cur.execute("""
                INSERT INTO facturas(id_cita,id_cliente,fecha,concepto,importe,pagada)
                VALUES (?,?,?,?,?,0)
            """, (
                id_cita,
                id_cliente,
                datetime.now().strftime("%d/%m/%Y"),
                "Consulta dental",
                50.0
            ))

            conn.commit()
            conn.close()
            win.destroy()
            refrescar()

        ttk.Button(win, text="💾 Crear factura", command=crear).pack(pady=10)

    # =====================================================
    # MARCAR COMO PAGADA
    # =====================================================
    def marcar_pagada():
        """Marca una factura como pagada"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona una factura", parent=v)
            return

        id_factura = tabla.item(sel[0])["values"][0]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("UPDATE facturas SET pagada=1 WHERE id=?", (id_factura,))
        conn.commit()
        conn.close()

        refrescar()
        messagebox.showinfo("✅ Éxito", "Factura marcada como pagada", parent=v)

    # =====================================================
    # GENERAR PDF
    # =====================================================
    def pdf():
        """Genera PDF de la factura seleccionada"""
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Aviso", "Selecciona una factura", parent=v)
            return

        id_factura = tabla.item(sel[0])["values"][0]
        generar_pdf_factura(id_factura)

    # =====================================================
    # BOTONES
    # =====================================================
    ttk.Button(frame, text="➕ Crear desde cita", command=nueva_desde_cita).grid(row=1, column=0, padx=10)
    ttk.Button(frame, text="✅ Marcar pagada", command=marcar_pagada).grid(row=1, column=1, padx=10)
    ttk.Button(frame, text="📄 Generar PDF", command=pdf).grid(row=1, column=2, padx=10)
    ttk.Button(frame, text="🔄 Refrescar", command=refrescar).grid(row=1, column=3, padx=10)

    # Botón para volver al menú principal
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy).grid(row=2, column=0, columnspan=6, pady=15)

    refrescar()


# =====================================================
# HISTORIAL DEL PACIENTE
# =====================================================

def ventana_historial_paciente(raiz, id_cliente=None):
    """Ventana que muestra todo el historial de un paciente"""
    v = tk.Toplevel(raiz)
    v.title("📋 Historial del Paciente")
    # NO hacemos la ventana modal para poder abrir varias a la vez
    centrar(v)

    canvas = fondo(v, "Patrón dental suave y profesional.png")
    frame = ttk.Frame(canvas, padding=30)
    canvas.create_window(960, 540, window=frame)

    # ========== SELECTOR DE CLIENTE ==========
    frame_selector = ttk.Frame(frame)
    frame_selector.grid(row=0, column=0, columnspan=2, pady=20)

    ttk.Label(frame_selector, text="Selecciona paciente:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

    # Obtenemos todos los clientes
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, apellidos FROM clientes ORDER BY nombre")
    clientes = cur.fetchall()
    conn.close()

    if not clientes:
        messagebox.showinfo("ℹ️ Aviso", "No hay clientes registrados", parent=v)
        v.destroy()
        return

    # Desplegable con clientes
    combo_clientes = ttk.Combobox(
        frame_selector,
        values=[f"{c[0]} - {c[1]} {c[2]}" for c in clientes],
        state="readonly",
        width=40,
        font=("Segoe UI", 12)
    )
    combo_clientes.pack(side="left", padx=10)

    # Si se pasó un ID, lo seleccionamos
    if id_cliente:
        for i, c in enumerate(clientes):
            if c[0] == id_cliente:
                combo_clientes.current(i)
                break
    else:
        combo_clientes.current(0)

    # ========== INFORMACIÓN DEL PACIENTE ==========
    frame_info = ttk.LabelFrame(frame, text="📝 Información del Paciente", padding=15)
    frame_info.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

    # Labels para mostrar info
    label_nombre = ttk.Label(frame_info, text="", font=("Segoe UI", 12))
    label_nombre.grid(row=0, column=0, sticky="w", pady=5)

    label_telefono = ttk.Label(frame_info, text="", font=("Segoe UI", 11))
    label_telefono.grid(row=1, column=0, sticky="w", pady=5)

    label_email = ttk.Label(frame_info, text="", font=("Segoe UI", 11))
    label_email.grid(row=2, column=0, sticky="w", pady=5)

    # ========== RESUMEN ==========
    frame_resumen = ttk.LabelFrame(frame, text="📊 Resumen", padding=15)
    frame_resumen.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

    label_total_citas = ttk.Label(frame_resumen, text="", font=("Segoe UI", 11))
    label_total_citas.grid(row=0, column=0, padx=20, pady=5)

    label_citas_pendientes = ttk.Label(frame_resumen, text="", font=("Segoe UI", 11))
    label_citas_pendientes.grid(row=0, column=1, padx=20, pady=5)

    label_total_gastado = ttk.Label(frame_resumen, text="", font=("Segoe UI", 11))
    label_total_gastado.grid(row=0, column=2, padx=20, pady=5)

    label_facturas_pendientes = ttk.Label(frame_resumen, text="", font=("Segoe UI", 11))
    label_facturas_pendientes.grid(row=0, column=3, padx=20, pady=5)

    # ========== CITAS DEL PACIENTE ==========
    frame_citas = ttk.LabelFrame(frame, text="📅 Historial de Citas", padding=10)
    frame_citas.grid(row=3, column=0, pady=10, sticky="nsew")

    cols_citas = ("ID", "Fecha", "Hora", "Dentista", "Motivo", "Estado")
    tabla_citas = ttk.Treeview(frame_citas, columns=cols_citas, show="headings", height=12)

    for c in cols_citas:
        tabla_citas.heading(c, text=c)
        tabla_citas.column(c, width=120, anchor="center")

    tabla_citas.pack(fill="both", expand=True)

    # Scrollbar para citas
    scroll_citas = ttk.Scrollbar(frame_citas, orient="vertical", command=tabla_citas.yview)
    scroll_citas.pack(side="right", fill="y")
    tabla_citas.configure(yscrollcommand=scroll_citas.set)

    # ========== FACTURAS DEL PACIENTE ==========
    frame_facturas = ttk.LabelFrame(frame, text="💰 Historial de Facturas", padding=10)
    frame_facturas.grid(row=3, column=1, pady=10, sticky="nsew")

    cols_facturas = ("ID", "Fecha", "Concepto", "Importe", "Pagada")
    tabla_facturas = ttk.Treeview(frame_facturas, columns=cols_facturas, show="headings", height=12)

    for c in cols_facturas:
        tabla_facturas.heading(c, text=c)
        tabla_facturas.column(c, width=120, anchor="center")

    tabla_facturas.pack(fill="both", expand=True)

    # Scrollbar para facturas
    scroll_facturas = ttk.Scrollbar(frame_facturas, orient="vertical", command=tabla_facturas.yview)
    scroll_facturas.pack(side="right", fill="y")
    tabla_facturas.configure(yscrollcommand=scroll_facturas.set)

    # Configurar pesos de columnas para que se expandan
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(3, weight=1)

    # ========== CARGAR DATOS ==========
    def cargar_historial():
        """Carga todo el historial del paciente seleccionado"""
        if not combo_clientes.get():
            return

        # Obtenemos el ID del cliente seleccionado
        id_cliente_sel = int(combo_clientes.get().split("-")[0].strip())

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # ===== INFORMACIÓN BÁSICA =====
        cur.execute("SELECT nombre, apellidos, telefono, email FROM clientes WHERE id=?", (id_cliente_sel,))
        cliente = cur.fetchone()

        label_nombre.config(text=f"👤 Paciente: {cliente[0]} {cliente[1]}")
        label_telefono.config(text=f"📞 Teléfono: {cliente[2]}")
        label_email.config(text=f"📧 Email: {cliente[3]}")

        # ===== RESUMEN DE CITAS =====
        cur.execute("SELECT COUNT(*) FROM citas WHERE id_cliente=?", (id_cliente_sel,))
        total_citas = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM citas WHERE id_cliente=? AND estado='Pendiente'", (id_cliente_sel,))
        citas_pendientes = cur.fetchone()[0]

        label_total_citas.config(text=f"📅 Total citas: {total_citas}")
        label_citas_pendientes.config(text=f"⏳ Pendientes: {citas_pendientes}")

        # ===== RESUMEN DE FACTURAS =====
        cur.execute("SELECT IFNULL(SUM(importe), 0) FROM facturas WHERE id_cliente=?", (id_cliente_sel,))
        total_gastado = cur.fetchone()[0]

        cur.execute("SELECT IFNULL(SUM(importe), 0) FROM facturas WHERE id_cliente=? AND pagada=0", (id_cliente_sel,))
        facturas_pendientes = cur.fetchone()[0]

        label_total_gastado.config(text=f"💰 Total gastado: {total_gastado:.2f}€")
        label_facturas_pendientes.config(text=f"⚠️ Pendiente pago: {facturas_pendientes:.2f}€")

        # ===== TABLA DE CITAS =====
        # Limpiamos tabla
        for i in tabla_citas.get_children():
            tabla_citas.delete(i)

        # Cargamos citas ordenadas por fecha (más recientes primero)
        query_citas = """
        SELECT citas.id, citas.fecha, citas.hora,
               dentistas.nombre || ' ' || dentistas.apellidos,
               citas.motivo, citas.estado
        FROM citas
        JOIN dentistas ON dentistas.id = citas.id_dentista
        WHERE citas.id_cliente = ?
        ORDER BY citas.fecha DESC, citas.hora DESC
        """

        for fila in cur.execute(query_citas, (id_cliente_sel,)):
            tabla_citas.insert("", "end", values=fila)

        # ===== TABLA DE FACTURAS =====
        # Limpiamos tabla
        for i in tabla_facturas.get_children():
            tabla_facturas.delete(i)

        # Cargamos facturas
        query_facturas = """
        SELECT id, fecha, concepto, importe, pagada
        FROM facturas
        WHERE id_cliente = ?
        ORDER BY fecha DESC
        """

        for fila in cur.execute(query_facturas, (id_cliente_sel,)):
            estado_pago = "Sí" if fila[4] == 1 else "No"
            tabla_facturas.insert("", "end", values=(
                fila[0], fila[1], fila[2], f"{fila[3]:.2f}€", estado_pago
            ))

        conn.close()

    # Botón para cargar/refrescar historial
    ttk.Button(frame_selector, text="🔄 Cargar historial", command=cargar_historial).pack(side="left", padx=10)

    # Cargar automáticamente al abrir
    cargar_historial()

    # ========== BOTÓN VOLVER ==========
    ttk.Button(frame, text="🔙 Volver al menú", command=v.destroy) \
        .grid(row=4, column=0, columnspan=2, pady=15)


# =====================================================
# MENÚ PRINCIPAL CON EMOJIS
# =====================================================

def menu():
    """Función principal que muestra el menú de inicio"""
    # Creamos la base de datos si no existe
    crear_bd()

    # Creamos la ventana principal
    raiz = tk.Tk()
    raiz.title("🦷 CLÍNICA DENTAL")
    centrar(raiz)

    # Ponemos fondo
    canvas = fondo(raiz, "Clínica dental moderna y profesional.png")

    # Título grande en el centro superior
    canvas.create_text(960, 180, text="🦷 CLÍNICA DENTAL", font=("Segoe UI", 48, "bold"), fill="#003366")

    def boton(y, txt, cmd):
        """Función auxiliar para crear botones centrados"""
        # Creamos el botón
        b = ttk.Button(raiz, text=txt, command=cmd)
        # Lo colocamos en el canvas en posición Y, centrado horizontalmente (960)
        canvas.create_window(960, y, window=b, width=320, height=60)

    # Creamos los botones del menú principal con emojis
    boton(320, "📊 Dashboard", lambda: ventana_dashboard(raiz))
    boton(410, "👥 Clientes", lambda: ventana_clientes(raiz))
    boton(500, "👨‍⚕️ Dentistas", lambda: ventana_dentistas(raiz))
    boton(590, "📅 Citas", lambda: ventana_citas(raiz))
    boton(680, "🦷 Materiales", lambda: ventana_materiales(raiz))
    boton(770, "💰 Facturas", lambda: ventana_facturas(raiz))
    boton(860, "📋 Historial Paciente", lambda: ventana_historial_paciente(raiz))
    boton(950, "❌ Salir", raiz.quit)

    # Iniciamos el bucle principal de la aplicación
    raiz.mainloop()


# Punto de entrada del programa
if __name__ == "__main__":
    menu()  # Llamamos a la función del menú principal