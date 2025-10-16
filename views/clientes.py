import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import random
import string

class ModuloClientes:
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.reparar_base_datos_clientes()

    def abrir_gestion_clientes(self):
        """Ventana simple de gestión de clientes"""
        top = tk.Toplevel(self.root)
        top.title("Gestión de Clientes - 'Nombre' Gym")
        top.geometry("800x500")
        
        # HACER LA VENTANA MODAL (se queda encima y bloquea la principal)
        top.transient(self.root)  # Indicar que es hija de la principal
        top.grab_set()  # Capturar todos los eventos
        top.focus_force()  # Forzar el foco

        # Centrar la ventana
        top.update_idletasks()
        x = (top.winfo_screenwidth() // 2) - (800 // 2)
        y = (top.winfo_screenheight() // 2) - (500 // 2)
        top.geometry(f'800x500+{x}+{y}')

        # Pestañas simples
        notebook = ttk.Notebook(top)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña 1: Registrar entrada
        tab_entrada = ttk.Frame(notebook)
        notebook.add(tab_entrada, text='Registrar Entrada')
        self.configurar_tab_entrada(tab_entrada)
        
        # Pestaña 2: Gestión de clientes
        tab_clientes = ttk.Frame(notebook)
        notebook.add(tab_clientes, text='Gestionar Clientes')
        self.configurar_tab_clientes(tab_clientes)
        
        # Pestaña 3: Membresías
        tab_membresias = ttk.Frame(notebook)
        notebook.add(tab_membresias, text='Membresías')
        self.configurar_tab_membresias(tab_membresias)

        # Pestaña 4: Registros de entrada
        tab_registros = ttk.Frame(notebook)
        notebook.add(tab_registros, text='Historial de Entradas')
        self.configurar_tab_registros_entrada(tab_registros)
    
    def configurar_tab_clientes(self, parent):
        """Pestaña simple para gestionar clientes"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        # Frame de botones superiores
        top_btn_frame = tk.Frame(frame)
        top_btn_frame.pack(fill='x', pady=(0, 10))
        
        # Botón para agregar cliente
        btn_nuevo = tk.Button(top_btn_frame, text="➕ Nuevo Cliente", 
                            command=self.abrir_nuevo_cliente,
                            bg='#3498db', fg='white')
        btn_nuevo.pack(side='left', padx=5)
        
        # Botón para eliminar cliente seleccionado
        btn_eliminar = tk.Button(top_btn_frame, text="🗑️ Eliminar Cliente", 
                            command=self.eliminar_cliente_seleccionado,
                            bg='#e74c3c', fg='white')
        btn_eliminar.pack(side='left', padx=5)
        
        # Botón para reactivar clientes
        btn_reactivar = tk.Button(top_btn_frame, text="♻️ Reactivar Cliente", 
                                command=self.reactivar_cliente_completo,
                                bg='#9b59b6', fg='white')
        btn_reactivar.pack(side='left', padx=5)

        # Botón para renovar membresia
        btn_renovar = tk.Button(top_btn_frame, text="🔄 Renovar Membresía", 
                            command=self.renovar_membresia,
                            bg='#f39c12', fg='white')
        btn_renovar.pack(side='left', padx=5)

        # Botón para actualizar
        btn_actualizar = tk.Button(top_btn_frame, text="🔄 Actualizar", 
                                command=lambda: self.cargar_clientes_en_treeview(tree),
                                bg='#2ecc71', fg='white')
        btn_actualizar.pack(side='right', padx=5)

        # Lista simple de clientes
        columns = ("numero", "nombre", "telefono", "estado")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree_clientes = tree  # Guardar referencia para usar en otras funciones
        
        tree.heading("numero", text="Número")
        tree.heading("nombre", text="Nombre")
        tree.heading("telefono", text="Teléfono")
        tree.heading("estado", text="Estado")
        
        tree.column("numero", width=80, anchor="center")
        tree.column("nombre", width=200)
        tree.column("telefono", width=120)
        tree.column("estado", width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True)
        
        # Cargar clientes
        self.cargar_clientes_en_treeview(tree)
        
        # Doble clic para editar (opcional)
        tree.bind('<Double-1>', lambda e: self.editar_cliente_seleccionado())

    def cargar_clientes_en_treeview(self, tree):
        """Método UNIFICADO para cargar clientes"""
        # Limpiar treeview
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # VERIFICAR ESTRUCTURA (solo una vez)
            cursor.execute("PRAGMA table_info(clientes)")
            columnas_existentes = [col[1] for col in cursor.fetchall()]
            
            if 'activo' not in columnas_existentes:
                cursor.execute("ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1")
                conn.commit()
            
            # CARGAR CON ESTADO
            cursor.execute("""
                SELECT numero_cliente, nombre, telefono, 
                    CASE WHEN activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
                FROM clientes 
                ORDER BY activo DESC, nombre
            """)
            
            for cliente in cursor.fetchall():
                numero, nombre, telefono, estado = cliente
                telefono_str = telefono if telefono else "N/A"
                item_id = tree.insert("", "end", values=(numero, nombre, telefono_str, estado))
                
                if estado == "Inactivo":
                    tree.item(item_id, tags=('inactive',))
                    
            tree.tag_configure('inactive', foreground='gray')
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar clientes: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def eliminar_cliente_seleccionado(self):
        """Eliminar (desactivar) el cliente seleccionado"""
        if not hasattr(self, 'tree_clientes'):
            messagebox.showwarning("Advertencia", "No hay lista de clientes cargada")
            return
        
        seleccion = self.tree_clientes.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un cliente primero")
            return
        
        # Obtener datos del cliente seleccionado
        item = seleccion[0]
        valores = self.tree_clientes.item(item, 'values')
        
        # DEPURACIÓN: Ver qué datos tenemos realmente
        print(f"Datos del item seleccionado: {valores}")
        print(f"Número de columnas: {len(valores)}")
        
        # VERIFICACIÓN MEJORADA: Diferentes patrones de datos
        if len(valores) >= 3:
            # Patrón 1: [numero, nombre, telefono, estado] (4 columnas)
            if len(valores) == 4:
                numero_cliente = valores[0]
                nombre_cliente = valores[1]
                estado_actual = valores[3]
            # Patrón 2: [numero, nombre, telefono] (3 columnas - clientes antiguos)
            elif len(valores) == 3:
                numero_cliente = valores[0]
                nombre_cliente = valores[1]
                estado_actual = "Activo"  # Asumir activo para clientes antiguos
            else:
                messagebox.showerror("Error", f"Formato de datos no reconocido. Longitud: {len(valores)}")
                return
        else:
            messagebox.showerror("Error", "Datos del cliente incompletos. Recargue la lista.")
            return
        
        # Verificar si ya está inactivo
        if "Inactivo" in str(estado_actual) or "❌" in str(estado_actual):
            messagebox.showinfo("Información", f"El cliente {nombre_cliente} ya está inactivo")
            return
        
        # Confirmación de eliminación
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar al cliente?\n\n"
            f"Cliente: {nombre_cliente}\n"
            f"Número: {numero_cliente}\n\n"
            "⚠️ Esta acción marcará al cliente como inactivo. "
            "El cliente no podrá registrar entradas pero se mantendrán "
            "sus registros históricos."
        )
        
        if not confirmacion:
            return
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # PRIMERO asegurarnos que la columna 'activo' existe
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'activo' not in columnas:
                cursor.execute("ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1")
                print("Columna 'activo' agregada a la tabla clientes")
            
            # Cancelar todas sus membresías activas
            cursor.execute("""
                UPDATE membresias 
                SET estado = 'cancelada' 
                WHERE cliente_id IN (
                    SELECT id FROM clientes WHERE numero_cliente = ?
                ) AND estado = 'activa'
            """, (numero_cliente,))

            # ELIMINACIÓN SEGURA: Marcar como inactivo
            cursor.execute("""
                UPDATE clientes 
                SET activo = 0 
                WHERE numero_cliente = ?
            """, (numero_cliente,))
            
            conn.commit()
            
            messagebox.showinfo("Éxito", 
                            f"Cliente eliminado correctamente\n"
                            f"👤 {nombre_cliente}\n"
                            f"🔢 {numero_cliente}\n\n"
                            "El cliente fue marcado como inactivo. "
                            "Sus registros históricos se mantienen.")
            
            # Actualizar la lista
            self.cargar_clientes_en_treeview(self.tree_clientes)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el cliente: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def editar_cliente_seleccionado(self):
        """Editar cliente seleccionado (opcional)"""
        seleccion = self.tree_clientes.selection()
        if not seleccion:
            return
        
        # Obtener datos del cliente seleccionado
        item = seleccion[0]
        valores = self.tree_clientes.item(item, 'values')
        numero_cliente = valores[0]
        nombre_actual = valores[1]
        telefono_actual = valores[2] if valores[2] != "N/A" else ""
        
        # Ventana de edición
        top = self.crear_ventana_modal(f"Editar Cliente: {numero_cliente}", 400, 250)
        
        frame = tk.Frame(top, padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text=f"Editando cliente: {numero_cliente}", 
                font=('Arial', 11, 'bold')).pack(pady=(0, 15))
        
        tk.Label(frame, text="Nombre:", font=('Arial', 10)).pack(anchor='w', pady=(5, 2))
        nombre_var = tk.StringVar(value=nombre_actual)
        entry_nombre = tk.Entry(frame, textvariable=nombre_var, width=30)
        entry_nombre.pack(pady=(0, 10))
        entry_nombre.focus()
        
        tk.Label(frame, text="Teléfono:", font=('Arial', 10)).pack(anchor='w', pady=(5, 2))
        telefono_var = tk.StringVar(value=telefono_actual)
        entry_telefono = tk.Entry(frame, textvariable=telefono_var, width=20)
        entry_telefono.pack(pady=(0, 20))
        
        def guardar_cambios():
            nuevo_nombre = nombre_var.get().strip()
            nuevo_telefono = telefono_var.get().strip()
            
            if not nuevo_nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE clientes 
                    SET nombre = ?, telefono = ?
                    WHERE numero_cliente = ?
                """, (nuevo_nombre, nuevo_telefono if nuevo_telefono else None, numero_cliente))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Cliente actualizado correctamente")
                top.destroy()
                self.cargar_clientes_en_treeview(self.tree_clientes)
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el cliente: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Frame para botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        btn_guardar = tk.Button(btn_frame, text="💾 Guardar", 
                            command=guardar_cambios,
                            bg='#27ae60', fg='white')
        btn_guardar.pack(side='left', padx=5)
        
        btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", 
                                command=top.destroy,
                                bg='#95a5a6', fg='white')
        btn_cancelar.pack(side='left', padx=5)
        
        # Enter para guardar
        entry_nombre.bind('<Return>', lambda e: guardar_cambios())
        entry_telefono.bind('<Return>', lambda e: guardar_cambios())
    
    def abrir_nuevo_cliente(self):
        """Ventana simple para nuevo cliente"""
        top = self.crear_ventana_modal("Nuevo Cliente", 400, 300)
        
        frame = tk.Frame(top, padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Nombre completo:", font=('Arial', 10)).pack(anchor='w', pady=(5, 2))
        nombre_var = tk.StringVar()
        entry_nombre = tk.Entry(frame, textvariable=nombre_var, width=30)
        entry_nombre.pack(pady=(0, 10))
        entry_nombre.focus()
        
        tk.Label(frame, text="Teléfono:", font=('Arial', 10)).pack(anchor='w', pady=(5, 2))
        telefono_var = tk.StringVar()
        entry_telefono = tk.Entry(frame, textvariable=telefono_var, width=20)
        entry_telefono.pack(pady=(0, 20))
        
        # ✅✅✅ FUNCIÓN COMPLETA PARA GUARDAR CLIENTE
        def guardar_cliente():
            nombre = nombre_var.get().strip()
            telefono = telefono_var.get().strip()
            
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                # GENERAR NÚMERO DE 4 DÍGITOS (0001-9999)
                cursor.execute("SELECT COALESCE(MAX(CAST(numero_cliente AS INTEGER)), 0) FROM clientes")
                ultimo_numero = cursor.fetchone()[0]
                
                # Si es el primer cliente o números se acabaron, reiniciar desde 1
                if ultimo_numero >= 9999:
                    # Buscar números disponibles (huecos)
                    cursor.execute("""
                        WITH numbers AS (
                            SELECT 1 as num
                            UNION ALL
                            SELECT num + 1 FROM numbers WHERE num < 9999
                        )
                        SELECT MIN(numbers.num)
                        FROM numbers
                        LEFT JOIN clientes ON numbers.num = CAST(clientes.numero_cliente AS INTEGER)
                        WHERE clientes.numero_cliente IS NULL
                        LIMIT 1
                    """)
                    nuevo_numero = cursor.fetchone()[0]
                    if nuevo_numero is None:
                        messagebox.showerror("Error", "No hay números disponibles. Contacte al administrador.")
                        return
                else:
                    nuevo_numero = ultimo_numero + 1
                
                # Formatear a 4 dígitos con ceros a la izquierda
                numero_cliente = f"{nuevo_numero:04d}"
                
                # Verificar que el número no exista (por si acaso)
                cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Error al generar número único. Intente nuevamente.")
                    return
                
                # Insertar nuevo cliente
                cursor.execute(
                    "INSERT INTO clientes (numero_cliente, nombre, telefono) VALUES (?, ?, ?)",
                    (numero_cliente, nombre, telefono if telefono else None)
                )
                
                conn.commit()
                messagebox.showinfo("Éxito", 
                                f"Cliente agregado correctamente\n"
                                f"✅ Número de cliente: {numero_cliente}\n"
                                f"👤 Nombre: {nombre}")
                
                # Cerrar ventana
                top.destroy()
                
                # Actualizar lista de clientes si está visible
                if hasattr(self, 'tree_clientes'):
                    self.cargar_clientes_en_treeview(self.tree_clientes)
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el cliente: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Frame para botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        btn_guardar = tk.Button(btn_frame, text="💾 Guardar", 
                            command=guardar_cliente,
                            bg='#27ae60', fg='white', font=('Arial', 10))
        btn_guardar.pack(side='left', padx=5)
        
        btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", 
                                command=top.destroy,
                                bg='#e74c3c', fg='white', font=('Arial', 10))
        btn_cancelar.pack(side='left', padx=5)
        
        # Enter para guardar
        entry_nombre.bind('<Return>', lambda e: guardar_cliente())
        entry_telefono.bind('<Return>', lambda e: guardar_cliente())
    
    def configurar_tab_membresias(self, parent):
        """Pestaña simple para ver membresías próximas a vencer"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Membresías que vencen en los próximos 7 días:", 
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Lista simple de membresías
        columns = ("cliente", "vencimiento", "estado")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        
        tree.heading("cliente", text="Cliente")
        tree.heading("vencimiento", text="Vencimiento")
        tree.heading("estado", text="Estado")
        
        tree.column("cliente", width=200)
        tree.column("vencimiento", width=150)
        tree.column("estado", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True)
        
        def on_doble_clic_membresia(event):
            selection = tree.selection()
            if selection:
                # Aquí puedes implementar renovación rápida
                item = selection[0]
                valores = tree.item(item, 'values')
                messagebox.showinfo("Renovación Rápida", 
                                f"Renovar membresía de {valores[0]}\n"
                                f"Vence: {valores[3]}")
                
        tree.bind('<Double-1>', on_doble_clic_membresia)

        # Cargar membresías próximas a vencer
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.nombre, m.fecha_vencimiento, m.estado
                FROM membresias m
                JOIN clientes c ON m.cliente_id = c.id
                WHERE m.estado = 'activa' 
                AND m.fecha_vencimiento BETWEEN date('now') AND date('now', '+7 days')
                ORDER BY m.fecha_vencimiento
            """)
            
            for membresia in cursor.fetchall():
                tree.insert("", "end", values=membresia)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar membresías: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def abrir_gestion_membresias(self):
        """Ventana para gestionar membresías de clientes"""
        top = self.crear_ventana_modal("Gestión de Membresías - 'Nombre' Gym", 900, 600)
        
        # Pestañas
        notebook = ttk.Notebook(top)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña 1: Asignar membresía
        tab_asignar = ttk.Frame(notebook)
        notebook.add(tab_asignar, text='Asignar Membresía')
        self.configurar_tab_asignar_membresia(tab_asignar)
        
        # Pestaña 2: Ver membresías activas
        tab_activas = ttk.Frame(notebook)
        notebook.add(tab_activas, text='Membresías Activas')
        self.configurar_tab_membresias_activas(tab_activas)
        
        # Pestaña 3: Historial de membresías
        tab_historial = ttk.Frame(notebook)
        notebook.add(tab_historial, text='Historial')
        self.configurar_tab_historial_membresias(tab_historial)

    def configurar_tab_asignar_membresia(self, parent):
        """Pestaña para asignar membresía a cliente"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        # Buscar cliente
        tk.Label(frame, text="Buscar Cliente:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        
        search_frame = tk.Frame(frame)
        search_frame.pack(fill='x', pady=(0, 10))
        
        self.busqueda_cliente_var = tk.StringVar()
        entry_busqueda = tk.Entry(search_frame, textvariable=self.busqueda_cliente_var, width=30)
        entry_busqueda.pack(side='left', padx=(0, 5))
        entry_busqueda.bind('<Return>', lambda e: self.buscar_cliente_para_membresia())
        
        btn_buscar = tk.Button(search_frame, text="🔍 Buscar", 
                            command=self.buscar_cliente_para_membresia)
        btn_buscar.pack(side='left')
        
        # Resultados de búsqueda
        tk.Label(frame, text="Clientes encontrados:", font=('Arial', 10)).pack(anchor='w', pady=(10, 5))
        
        self.lista_clientes = tk.Listbox(frame, height=6)
        self.lista_clientes.pack(fill='x', pady=(0, 10))
        self.lista_clientes.clientes_data = []
        self.lista_clientes.bind('<<ListboxSelect>>', self.seleccionar_cliente)
        
        # Info del cliente seleccionado
        self.info_cliente_frame = tk.LabelFrame(frame, text="Cliente Seleccionado", font=('Arial', 10, 'bold'))
        self.info_cliente_frame.pack(fill='x', pady=(0, 10))
        self.info_cliente_label = tk.Label(self.info_cliente_frame, text="Ningún cliente seleccionado", font=('Arial', 9))
        self.info_cliente_label.pack(padx=10, pady=10)
        
        # Formulario de membresía
        form_frame = tk.LabelFrame(frame, text="Datos de la Membresía", font=('Arial', 10, 'bold'))
        form_frame.pack(fill='x', pady=(0, 10))
        
        # Tipo de membresía
        tk.Label(form_frame, text="Tipo de Membresía:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.tipo_membresia_var = tk.StringVar(value="Mensual")
        opciones_membresia = ["Mensual", "Trimestral", "Semestral", "Anual", "Estudiante", "Semanal", "Pareja", "Clase", "Plan Básico", "Plus", "Pro"]
        combo_membresia = ttk.Combobox(form_frame, textvariable=self.tipo_membresia_var, 
                                    values=opciones_membresia, state="readonly", width=15)
        combo_membresia.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        # Duración y precio
        tk.Label(form_frame, text="Duración (días):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.duracion_var = tk.StringVar(value="30")
        entry_duracion = tk.Entry(form_frame, textvariable=self.duracion_var, width=10)
        entry_duracion.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        tk.Label(form_frame, text="Precio $:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.precio_var = tk.StringVar(value="500")
        entry_precio = tk.Entry(form_frame, textvariable=self.precio_var, width=10)
        entry_precio.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        
        # Botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        btn_asignar = tk.Button(btn_frame, text="💳 Asignar Membresía", 
                            command=self.asignar_membresia,
                            bg='#27ae60', fg='white', font=('Arial', 11))
        btn_asignar.pack(side='left', padx=5)
        
        btn_limpiar = tk.Button(btn_frame, text="🔄 Limpiar", 
                            command=self.limpiar_formulario_membresia,
                            bg='#f39c12', fg='white')
        btn_limpiar.pack(side='left', padx=5)

    def buscar_cliente_para_membresia(self):
        """Buscar clientes para asignar membresía - SOLO ACTIVOS"""
        query = self.busqueda_cliente_var.get().strip()
        
        if not query:
            messagebox.showwarning("Advertencia", "Ingrese un nombre o número de cliente")
            return
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # ✅ SOLO buscar clientes ACTIVOS
            if query.isdigit() and len(query) == 4:
                cursor.execute("""
                    SELECT id, numero_cliente, nombre, telefono 
                    FROM clientes 
                    WHERE numero_cliente = ? AND activo = 1
                """, (query,))
            else:
                cursor.execute("""
                    SELECT id, numero_cliente, nombre, telefono 
                    FROM clientes 
                    WHERE nombre LIKE ? AND activo = 1
                    ORDER BY nombre
                """, (f"%{query}%",))
            
            clientes = cursor.fetchall()
            
            # Limpiar lista
            self.lista_clientes.delete(0, tk.END)
            self.lista_clientes.clientes_data = []
            
            # Mostrar resultados
            for cliente in clientes:
                cliente_id, numero, nombre, telefono = cliente
                display_text = f"{numero} - {nombre}"
                if telefono:
                    display_text += f" ({telefono})"
                
                self.lista_clientes.insert(tk.END, display_text)
                self.lista_clientes.clientes_data.append(cliente)
                
            if not clientes:
                self.lista_clientes.insert(tk.END, "No se encontraron clientes activos")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar clientes: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def seleccionar_cliente(self, event):
        """Cuando se selecciona un cliente de la lista"""
        seleccion = self.lista_clientes.curselection()
        if not seleccion:
            return
        
        cliente_data = self.lista_clientes.clientes_data[seleccion[0]]
        cliente_id, numero, nombre, telefono = cliente_data

        # Mostrar info del cliente
        info_text = f"Cliente: {nombre}\nNúmero: {numero}"
        if telefono:
            info_text += f"\nTeléfono: {telefono}"
        
        # Verificar si ya tiene membresía activa
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tipo_membresia, fecha_vencimiento 
                FROM membresias 
                WHERE cliente_id = ? AND estado = 'activa'
                ORDER BY fecha_vencimiento DESC LIMIT 1
            """, (cliente_id,))
            
            membresia = cursor.fetchone()
            if membresia:
                tipo, vencimiento = membresia
                info_text += f"\n\n⚠️ YA TIENE MEMBRESÍA ACTIVA\nTipo: {tipo}\nVence: {vencimiento}"
                
        except Exception as e:
            print(f"Error al verificar membresía: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        self.info_cliente_label.config(text=info_text)
        self.cliente_seleccionado_id = cliente_id

    def asignar_membresia(self):
        """Asignar una nueva membresía al cliente seleccionado"""
        if not hasattr(self, 'cliente_seleccionado_id'):
            messagebox.showwarning("Advertencia", "Seleccione un cliente primero")
            return
        
        try:
            # Validar datos
            duracion = int(self.duracion_var.get())
            precio = float(self.precio_var.get())
            tipo_membresia = self.tipo_membresia_var.get()
            
            if duracion <= 0 or precio < 0:
                messagebox.showerror("Error", "Duración y precio deben ser mayores a 0")
                return
            
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Calcular fechas
            fecha_inicio = datetime.now().strftime("%Y-%m-%d")
            fecha_vencimiento = (datetime.now() + timedelta(days=duracion)).strftime("%Y-%m-%d")
            
            # Insertar membresía
            cursor.execute("""
                INSERT INTO membresias (cliente_id, tipo_membresia, fecha_inicio, fecha_vencimiento, precio, estado)
                VALUES (?, ?, ?, ?, ?, 'activa')
            """, (self.cliente_seleccionado_id, tipo_membresia, fecha_inicio, fecha_vencimiento, precio))
            
            conn.commit()
            
            messagebox.showinfo("Éxito", 
                            f"Membresía asignada correctamente\n"
                            f"Tipo: {tipo_membresia}\n"
                            f"Vencimiento: {fecha_vencimiento}\n"
                            f"Precio: ${precio}")
            
            self.limpiar_formulario_membresia()
            
        except ValueError:
            messagebox.showerror("Error", "Duración y precio deben ser números válidos")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo asignar la membresía: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def limpiar_formulario_membresia(self):
        """Limpiar el formulario de membresía"""
        self.busqueda_cliente_var.set("")
        self.lista_clientes.delete(0, tk.END)
        self.lista_clientes.clientes_data = []
        self.info_cliente_label.config(text="Ningún cliente seleccionado")
        if hasattr(self, 'cliente_seleccionado_id'):
            delattr(self, 'cliente_seleccionado_id')
        
        # Valores por defecto
        self.tipo_membresia_var.set("Mensual")
        self.duracion_var.set("30")
        self.precio_var.set("500")

    def configurar_tab_membresias_activas(self, parent):
        """Pestaña para ver membresías activas"""
        if hasattr(self, 'tree_membresias') and self.tree_membresias.winfo_exists():
            self.tree_membresias.destroy()
        
        if hasattr(self, 'btn_frame_membresias') and self.btn_frame_membresias.winfo_exists():
            self.btn_frame_membresias.destroy()

        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        # Frame de botones superiores
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill='x', pady=(0, 10))
        self.btn_frame_membresias = btn_frame
        
        # Botón para editar membresía 
        btn_editar = tk.Button(btn_frame, text="✏️ Editar Membresía", 
                            command=self.editar_membresia_seleccionada,
                            bg='#3498db', fg='white')
        btn_editar.pack(side='left', padx=5)

        # Botón para eliminar membresía
        btn_cancelar = tk.Button(btn_frame, text="🗑️ Cancelar Membresía", 
                            command=self.cancelar_membresia_seleccionada,
                            bg='#e74c3c', fg='white')
        btn_cancelar.pack(side='left', padx=5)
        
        # Treeview para membresías activas
        columns = ("id", "cliente", "tipo", "inicio", "vencimiento", "dias_restantes", "precio")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree_membresias = tree  # Guardar referencia
        
        tree.heading("cliente", text="Cliente")
        tree.heading("tipo", text="Tipo")
        tree.heading("inicio", text="Inicio")
        tree.heading("vencimiento", text="Vencimiento")
        tree.heading("dias_restantes", text="Días Restantes")
        tree.heading("precio", text="Precio")
        
        # Ocultar la columna ID
        tree.column("id", width=0, stretch=False)  # ← ESTO OCULTA EL ID

        tree.column("cliente", width=150)
        tree.column("tipo", width=100)
        tree.column("inicio", width=100)
        tree.column("vencimiento", width=100)
        tree.column("dias_restantes", width=100)
        tree.column("precio", width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True)
        
         # Cargar datos
        self.cargar_datos_membresias_activas()

    def cargar_datos_membresias_activas(self):
        """Cargar datos en el treeview de membresías activas (sin recrear la interfaz)"""
        if not hasattr(self, 'tree_membresias'):
            return
        
        # Limpiar treeview existente
        for item in self.tree_membresias.get_children():
            self.tree_membresias.delete(item)
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT m.id, c.nombre, m.tipo_membresia, m.fecha_inicio, m.fecha_vencimiento, m.precio
                FROM membresias m
                JOIN clientes c ON m.cliente_id = c.id
                WHERE m.estado = 'activa'
                ORDER BY m.fecha_vencimiento
            """)
            
            for membresia in cursor.fetchall():
                membresia_id, nombre, tipo, inicio, vencimiento, precio = membresia
                
                # Calcular días restantes
                vencimiento_date = datetime.strptime(vencimiento, "%Y-%m-%d")
                dias_restantes = (vencimiento_date - datetime.now()).days
                
                if dias_restantes <= 3:
                    dias_text = f"⚠️ {dias_restantes}"
                else:
                    dias_text = str(dias_restantes)
                
                self.tree_membresias.insert("", "end", values=(
                    membresia_id, nombre, tipo, inicio, vencimiento, dias_text, f"${precio}"
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar membresías: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def editar_membresia_seleccionada(self):
        """Editar una membresía existente en lugar de crear una nueva"""
        if not hasattr(self, 'tree_membresias'):
            messagebox.showwarning("Advertencia", "Primero debe abrir la gestión de membresías")
            return
        
        seleccion = self.tree_membresias.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una membresía primero")
            return
        
        # Obtener membresía seleccionada
        item = seleccion[0]
        valores = self.tree_membresias.item(item, 'values')
        
        # Los valores ahora son: (id, cliente, tipo, inicio, vencimiento, dias_restantes, precio)
        membresia_id = valores[0]  # ID está en la posición 0 (pero oculto)
        nombre_cliente = valores[1]  # Cliente en posición 1
        tipo_actual = valores[2]    # Tipo en posición 2
        inicio_actual = valores[3]  # Inicio en posición 3
        vencimiento_actual = valores[4]  # Vencimiento en posición 4
        precio_actual = valores[6].replace('$', '')  # Precio en posición 6 (quitamos $)
        
        # Crear ventana de edición
        top = self.crear_ventana_modal(f"Editar Membresía - {nombre_cliente}", 500, 400)
        
        frame = tk.Frame(top, padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text=f"Editando membresía de: {nombre_cliente}", 
                font=('Arial', 12, 'bold'), fg='#2c3e50').pack(pady=(0, 10))
        
        # Formulario de edición
        form_frame = tk.LabelFrame(frame, text="Datos de la Membresía", font=('Arial', 10, 'bold'))
        form_frame.pack(fill='x', pady=(0, 15))
        
        # Tipo de membresía
        tk.Label(form_frame, text="Tipo de Membresía:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        tipo_var = tk.StringVar(value=tipo_actual)
        opciones_membresia = ["Mensual", "Trimestral", "Semestral", "Anual", "Estudiante", "Semanal", "Pareja", "Clase", "Plan Básico", "Plus", " Pro"]
        combo_tipo = ttk.Combobox(form_frame, textvariable=tipo_var, values=opciones_membresia, state="readonly", width=15)
        combo_tipo.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        # Fecha de inicio
        tk.Label(form_frame, text="Fecha Inicio:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        inicio_var = tk.StringVar(value=inicio_actual)
        entry_inicio = tk.Entry(form_frame, textvariable=inicio_var, width=12)
        entry_inicio.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        # Fecha de vencimiento
        tk.Label(form_frame, text="Fecha Vencimiento:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        vencimiento_var = tk.StringVar(value=vencimiento_actual)
        entry_vencimiento = tk.Entry(form_frame, textvariable=vencimiento_var, width=12)
        entry_vencimiento.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        
        # Precio
        tk.Label(form_frame, text="Precio $:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        precio_var = tk.StringVar(value=precio_actual.replace('$', ''))  # Quitar el símbolo $
        entry_precio = tk.Entry(form_frame, textvariable=precio_var, width=10)
        entry_precio.grid(row=3, column=1, padx=10, pady=5, sticky='w')
        
        def actualizar_membresia():
            """Actualizar la membresía existente"""
            try:
                nuevo_tipo = tipo_var.get()
                nuevo_inicio = inicio_var.get()
                nuevo_vencimiento = vencimiento_var.get()
                nuevo_precio = float(precio_var.get())
                
                # Validaciones
                if nuevo_precio < 0:
                    messagebox.showerror("Error", "El precio debe ser mayor a 0")
                    return
                
                # Verificar formato de fechas
                try:
                    datetime.strptime(nuevo_inicio, "%Y-%m-%d")
                    datetime.strptime(nuevo_vencimiento, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Formato de fecha incorrecto. Use YYYY-MM-DD")
                    return
                
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                # ACTUALIZAR membresía existente
                cursor.execute("""
                    UPDATE membresias 
                    SET tipo_membresia = ?, fecha_inicio = ?, fecha_vencimiento = ?, precio = ?
                    WHERE id = ?
                """, (nuevo_tipo, nuevo_inicio, nuevo_vencimiento, nuevo_precio, membresia_id))
                
                conn.commit()
                
                messagebox.showinfo("Éxito", f"Membresía actualizada correctamente")
            
                top.destroy()
                
                # SOLO ACTUALIZAR DATOS, NO RECREAR LA INTERFAZ
                self.cargar_datos_membresias_activas()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar la membresía: {str(e)}")
            
        # Botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
            
        btn_actualizar = tk.Button(btn_frame, text="💾 Actualizar", 
                                command=actualizar_membresia,
                                bg='#27ae60', fg='white')
        btn_actualizar.pack(side='left', padx=5)
            
        btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", 
                                command=top.destroy,
                                bg='#e74c3c', fg='white')
        btn_cancelar.pack(side='left', padx=5)

    def cancelar_membresia_seleccionada(self):
        """Cancelar una membresía activa"""
        if not hasattr(self, 'tree_membresias'):
            messagebox.showwarning("Advertencia", "Primero debe abrir la gestión de membresías")
            return
        
        seleccion = self.tree_membresias.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una membresía primero")
            return
        
        item = seleccion[0]
        valores = self.tree_membresias.item(item, 'values')
        
        if len(valores) < 7:
            messagebox.showerror("Error", "Datos de membresía incompletos")
            return
        
        membresia_id = valores[0]
        nombre_cliente = valores[1]
        tipo = valores[2]
        vencimiento = valores[4]
        
        if messagebox.askyesno("Confirmar Cancelación", 
                            f"¿Está seguro de cancelar la membresía de {nombre_cliente}?\n\n"
                            f"Tipo: {tipo}\n"
                            f"Vencimiento: {vencimiento}\n\n"
                            "Esta acción no se puede deshacer."):
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE membresias SET estado = 'cancelada' WHERE id = ?
                """, (membresia_id,))
                
                conn.commit()
                messagebox.showinfo("Éxito", f"Membresía de {nombre_cliente} cancelada correctamente")
                
                # ✅ SOLO ACTUALIZAR DATOS, NO RECREAR LA INTERFAZ
                self.cargar_datos_membresias_activas()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cancelar la membresía: {str(e)}")

    def configurar_tab_historial_membresias(self, parent):
        """Pestaña para ver historial de membresías"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        # Treeview para historial
        columns = ("cliente", "tipo", "inicio", "vencimiento", "estado", "precio")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        tree.heading("cliente", text="Cliente")
        tree.heading("tipo", text="Tipo")
        tree.heading("inicio", text="Inicio")
        tree.heading("vencimiento", text="Vencimiento")
        tree.heading("estado", text="Estado")
        tree.heading("precio", text="Precio")
        
        tree.column("cliente", width=150)
        tree.column("tipo", width=100)
        tree.column("inicio", width=100)
        tree.column("vencimiento", width=100)
        tree.column("estado", width=100)
        tree.column("precio", width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True)
        
        # Cargar historial
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.nombre, m.tipo_membresia, m.fecha_inicio, m.fecha_vencimiento, m.estado, m.precio
                FROM membresias m
                JOIN clientes c ON m.cliente_id = c.id
                ORDER BY m.fecha_inicio DESC
            """)
            
            for membresia in cursor.fetchall():
                tree.insert("", "end", values=membresia)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar historial: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def configurar_tab_registros_entrada(self, parent):
        """Pestaña para visualizar el historial de entradas de clientes"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        # Frame de filtros
        filtros_frame = tk.Frame(frame)
        filtros_frame.pack(fill='x', pady=(0, 10))
        
        # Filtro por fecha
        tk.Label(filtros_frame, text="Filtrar por fecha:", font=('Arial', 9)).grid(row=0, column=0, sticky='w', padx=(0, 5))
        
        self.filtro_fecha_var = tk.StringVar(value="hoy")
        opciones_fecha = ["hoy", "ayer", "esta semana", "este mes", "todos"]
        combo_fecha = ttk.Combobox(filtros_frame, textvariable=self.filtro_fecha_var, 
                                values=opciones_fecha, state="readonly", width=12)
        combo_fecha.grid(row=0, column=1, padx=(0, 15))
        combo_fecha.bind('<<ComboboxSelected>>', lambda e: self.cargar_registros_entrada())
        
        # Filtro por cliente
        tk.Label(filtros_frame, text="Filtrar por cliente:", font=('Arial', 9)).grid(row=0, column=2, sticky='w', padx=(0, 5))
        
        self.filtro_cliente_var = tk.StringVar()
        entry_cliente = tk.Entry(filtros_frame, textvariable=self.filtro_cliente_var, width=20)
        entry_cliente.grid(row=0, column=3, padx=(0, 15))
        entry_cliente.bind('<KeyRelease>', lambda e: self.cargar_registros_entrada())
        
        # Botón de actualizar
        btn_actualizar = tk.Button(filtros_frame, text="🔄 Actualizar", 
                                command=self.cargar_registros_entrada,
                                bg='#3498db', fg='white', font=('Arial', 9))
        btn_actualizar.grid(row=0, column=4)
        
        # Treeview para registros de entrada
        columns = ("fecha", "hora", "cliente", "numero", "usuario")
        self.tree_registros = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        
        self.tree_registros.heading("fecha", text="Fecha")
        self.tree_registros.heading("hora", text="Hora")
        self.tree_registros.heading("cliente", text="Cliente")
        self.tree_registros.heading("numero", text="Número Cliente")
        self.tree_registros.heading("usuario", text="Registrado por")
        
        self.tree_registros.column("fecha", width=100, anchor="center")
        self.tree_registros.column("hora", width=80, anchor="center")
        self.tree_registros.column("cliente", width=180)
        self.tree_registros.column("numero", width=100, anchor="center")
        self.tree_registros.column("usuario", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree_registros.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_registros.configure(yscrollcommand=scrollbar.set)
        self.tree_registros.pack(fill="both", expand=True)
        
        # Estadísticas
        self.stats_frame = tk.Frame(frame)
        self.stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_label = tk.Label(self.stats_frame, text="", font=('Arial', 9, 'bold'), fg='#2c3e50')
        self.stats_label.pack()
        
        # Cargar datos iniciales
        self.cargar_registros_entrada()

    def cargar_registros_entrada(self):
        """Cargar registros de entrada con hora formateada correctamente"""
        # Limpiar treeview
        for item in self.tree_registros.get_children():
            self.tree_registros.delete(item)
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Importar función de formateo
            from utils.fechas import formatear_fecha_hora_legible
            
            # Construir query con filtros
            query = """
                SELECT re.fecha_entrada, c.nombre, c.numero_cliente, u.nombre
                FROM registros_entrada re
                JOIN clientes c ON re.cliente_id = c.id
                LEFT JOIN usuarios u ON re.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            
            query += " ORDER BY re.fecha_entrada DESC"
            
            cursor.execute(query, params)
            registros = cursor.fetchall()
            
            # Insertar registros con hora formateada
            for registro in registros:
                fecha_completa, cliente, numero, usuario = registro
                
                # Formatear fecha y hora
                fecha_formateada = formatear_fecha_hora_legible(fecha_completa)
                
                # Separar fecha y hora si es necesario
                if ' ' in fecha_formateada:
                    fecha = fecha_formateada[:10]
                    hora = fecha_formateada[11:]
                else:
                    fecha = fecha_formateada
                    hora = ""
                
                self.tree_registros.insert("", "end", values=(fecha, hora, cliente, numero, usuario))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar registros: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def actualizar_estadisticas_registros(self, total, filtro_fecha):
        """Actualizar label con estadísticas"""
        texto_filtro = ""
        if filtro_fecha == "hoy":
            texto_filtro = "hoy"
        elif filtro_fecha == "ayer":
            texto_filtro = "ayer"
        elif filtro_fecha == "esta semana":
            texto_filtro = "esta semana"
        elif filtro_fecha == "este mes":
            texto_filtro = "este mes"
        else:
            texto_filtro = "todas las fechas"
        
        self.stats_label.config(text=f"Total de entradas registradas ({texto_filtro}): {total}")

    def configurar_tab_entrada(self, parent):
        """Pestaña simple para registrar entrada por número de cliente (ACTUALIZADA)"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Registro Rápido de Entrada", 
                font=('Arial', 12, 'bold'), fg='#2c3e50').pack(pady=(0, 10))
        
        tk.Label(frame, text="Número de Cliente:", font=('Arial', 11)).pack(pady=5)
        
        self.numero_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.numero_var, font=('Arial', 14), width=15, justify='center')
        entry.pack(pady=5)
        entry.bind('<Return>', lambda e: self.registrar_entrada())
        entry.focus()
        
        btn_entrada = tk.Button(frame, text="🎯 Registrar Entrada", 
                            command=self.registrar_entrada,
                            bg='#27ae60', fg='white', font=('Arial', 12))
        btn_entrada.pack(pady=10)
        
        # Área de mensajes
        self.mensaje_label = tk.Label(frame, text="", font=('Arial', 10))
        self.mensaje_label.pack(pady=5)
        
        # Info del último registro (NUEVO)
        self.ultimo_registro_frame = tk.LabelFrame(frame, text="Último Registro", font=('Arial', 9))
        self.ultimo_registro_frame.pack(fill='x', pady=(10, 0))
        self.ultimo_registro_label = tk.Label(self.ultimo_registro_frame, text="No hay registros recientes", 
                                            font=('Arial', 8))
        self.ultimo_registro_label.pack(padx=5, pady=5)

    def registrar_entrada(self):
        """Registrar entrada de cliente por número - CON HORA DEL SISTEMA"""
        numero = self.numero_var.get().strip()
        
        if not numero:
            self.mensaje_label.config(text="Ingrese el número de cliente", fg='red')
            return
        
        if not numero.isdigit() or len(numero) != 4:
            self.mensaje_label.config(text="❌ Número debe tener 4 dígitos", fg='red')
            return
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # OBTENER HORA DEL SISTEMA LOCAL - ¡SIMPLIFICADO!
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hora_actual = datetime.now().strftime("%H:%M")  # Solo hora:minuto
            
            # Buscar cliente 
            cursor.execute("""
                SELECT c.id, c.nombre, m.fecha_vencimiento, m.estado 
                FROM clientes c 
                LEFT JOIN membresias m ON c.id = m.cliente_id AND m.estado = 'activa'
                WHERE c.numero_cliente = ? AND c.activo = 1
                ORDER BY m.fecha_vencimiento DESC LIMIT 1
            """, (numero,))
            
            cliente = cursor.fetchone()
            
            if not cliente:
                self.mensaje_label.config(text="❌ Cliente no encontrado", fg='red')
                return
            
            cliente_id, nombre, fecha_vencimiento, estado = cliente
            
            # Verificar membresía
            if not fecha_vencimiento or estado != 'activa':
                self.mensaje_label.config(text="⚠️ Membresía vencida o inactiva", fg='orange')
                return
            
            # ✅ Asegurar que se use el ID correcto del usuario
            usuario_id = self.user_info['id']

            # Registrar entrada CON HORA DEL SISTEMA
            cursor.execute("""
                INSERT INTO registros_entrada (cliente_id, usuario_id, fecha_entrada) 
                VALUES (?, ?, ?)
            """, (cliente_id, self.user_info['id'], fecha_hora_actual))
            
            conn.commit()
            
            # Mensaje de éxito con hora actual
            self.mensaje_label.config(text=f"✅ {nombre} - Entrada registrada a las {hora_actual}", fg='green')
            
            # Actualizar info del último registro
            self.ultimo_registro_label.config(
                text=f"Cliente: {nombre}\n"
                    f"Número: {numero}\n"
                    f"Fecha: {fecha_hora_actual[:10]}\n"
                    f"Hora: {hora_actual}\n"
                    f"Registrado por: {self.user_info['nombre']}"
            )
            
            self.numero_var.set("")
            
            # Actualizar automáticamente la pestaña de registros
            if hasattr(self, 'tree_registros'):
                self.cargar_registros_entrada()
                
        except Exception as e:
            self.mensaje_label.config(text=f"Error: {str(e)}", fg='red')
        finally:
            if 'conn' in locals():
                conn.close()

    def reactivar_cliente_completo(self):
        """Reactivar cliente y asignarle membresía nueva"""
        seleccion = self.tree_clientes.selection()
        if not seleccion:
            return
        
        item = seleccion[0]
        valores = self.tree_clientes.item(item, 'values')
        
        if len(valores) < 4:
            return
        
        numero_cliente = valores[0]
        nombre_cliente = valores[1]
        estado = valores[3]
        
        if "Inactivo" not in estado:
            return
        
        # Reactivar el cliente
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE clientes SET activo = 1 WHERE numero_cliente = ?
            """, (numero_cliente,))
            
            conn.commit()
            
            # Preguntar si quiere asignar membresía
            if messagebox.askyesno("Reactivar Cliente", 
                                f"Cliente {nombre_cliente} reactivado.\n\n"
                                "¿Desea asignarle una membresía nueva?"):
                # Buscar el ID del cliente reactivado
                cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
                cliente_id = cursor.fetchone()[0]
                self.cliente_seleccionado_id = cliente_id
                
                # Abrir ventana de asignación de membresía
                self.abrir_gestion_membresias()
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reactivar el cliente: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def renovar_membresia(self):
        """Renovar la membresía de un cliente existente"""
        if not hasattr(self, 'tree_clientes'):
            messagebox.showwarning("Advertencia", "Primero debe abrir la gestión de clientes")
            return
        
        seleccion = self.tree_clientes.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un cliente primero")
            return
        
        # Obtener datos del cliente
        item = seleccion[0]
        valores = self.tree_clientes.item(item, 'values')
        numero_cliente = valores[0]
        nombre_cliente = valores[1]
        
        try:
            # ✅ CONEXIÓN PRINCIPAL que se mantendrá abierta
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Obtener ID del cliente
            cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
            resultado = cursor.fetchone()
            
            if not resultado:
                messagebox.showerror("Error", "No se pudo encontrar el ID del cliente")
                conn.close()  # ✅ Cerrar conexión si hay error
                return
            
            cliente_id = resultado[0]
            
            # Verificar membresía actual
            cursor.execute("""
                SELECT m.id, m.tipo_membresia, m.fecha_vencimiento, m.precio, m.estado
                FROM membresias m
                WHERE m.cliente_id = ? 
                ORDER BY m.fecha_vencimiento DESC LIMIT 1
            """, (cliente_id,))
            
            membresia_actual = cursor.fetchone()
            
            if not membresia_actual:
                messagebox.showinfo("Información", 
                                f"El cliente {nombre_cliente} no tiene membresías registradas.\n"
                                "Use la opción 'Asignar Membresía' en lugar de renovar.")
                conn.close()  # ✅ Cerrar conexión
                return
            
            membresia_id, tipo_actual, vencimiento_actual, precio_actual, estado = membresia_actual
            
            # Crear ventana de renovación
            top = self.crear_ventana_modal(f"Renovar Membresía - {nombre_cliente}", 500, 400)
            
            frame = tk.Frame(top, padx=20, pady=20)
            frame.pack(fill='both', expand=True)
            
            # Información de la membresía actual
            tk.Label(frame, text=f"Renovación para: {nombre_cliente}", 
                    font=('Arial', 12, 'bold'), fg='#2c3e50').pack(pady=(0, 10))
            
            info_frame = tk.LabelFrame(frame, text="Membresía Actual", font=('Arial', 10))
            info_frame.pack(fill='x', pady=(0, 15))
            
            info_text = f"Tipo: {tipo_actual}\nVencimiento: {vencimiento_actual}\nEstado: {estado}"
            if estado == 'activa':
                info_text += " ✅"
            else:
                info_text += " ❌"
                
            tk.Label(info_frame, text=info_text, font=('Arial', 9)).pack(padx=10, pady=10)
            
            # Formulario de renovación
            form_frame = tk.LabelFrame(frame, text="Nueva Membresía", font=('Arial', 10, 'bold'))
            form_frame.pack(fill='x', pady=(0, 15))
            
            # Tipo de membresía
            tk.Label(form_frame, text="Tipo de Membresía:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
            tipo_var = tk.StringVar(value=tipo_actual)
            opciones_membresia = ["Mensual", "Trimestral", "Semestral", "Anual", "Estudiante", "Semanal", "Pareja", "Clase", "Plan Básico", "Plus", "Pro"]
            combo_tipo = ttk.Combobox(form_frame, textvariable=tipo_var, values=opciones_membresia, state="readonly", width=15)
            combo_tipo.grid(row=0, column=1, padx=10, pady=5, sticky='w')
            
            # Duración
            tk.Label(form_frame, text="Duración (días):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
            duracion_var = tk.StringVar(value="30")
            entry_duracion = tk.Entry(form_frame, textvariable=duracion_var, width=10)
            entry_duracion.grid(row=1, column=1, padx=10, pady=5, sticky='w')
            
            # Precio
            tk.Label(form_frame, text="Precio $:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
            precio_var = tk.StringVar(value=str(precio_actual))
            entry_precio = tk.Entry(form_frame, textvariable=precio_var, width=10)
            entry_precio.grid(row=2, column=1, padx=10, pady=5, sticky='w')
            
            # Fecha de inicio (puede ser hoy o desde el vencimiento)
            tk.Label(form_frame, text="Iniciar desde:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
            inicio_var = tk.StringVar(value="hoy")
            opciones_inicio = ["hoy", "después del vencimiento"]
            combo_inicio = ttk.Combobox(form_frame, textvariable=inicio_var, values=opciones_inicio, state="readonly", width=20)
            combo_inicio.grid(row=3, column=1, padx=10, pady=5, sticky='w')
            
            def procesar_renovacion():
                """Procesar la renovación - CON NUEVA CONEXIÓN"""
                try:
                    # ✅ CREAR NUEVA CONEXIÓN dentro de esta función
                    conn_interna = sqlite3.connect("data/inventario.db")
                    cursor_interna = conn_interna.cursor()
                    
                    tipo = tipo_var.get()
                    duracion = int(duracion_var.get())
                    precio = float(precio_var.get())
                    inicio_opcion = inicio_var.get()
                    
                    if duracion <= 0 or precio < 0:
                        messagebox.showerror("Error", "Duración y precio deben ser mayores a 0")
                        conn_interna.close()
                        return
                    
                    from datetime import datetime, timedelta
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    
                    if inicio_opcion == "hoy" or estado != 'activa':
                        fecha_inicio = fecha_hoy
                    else:
                        fecha_inicio = (datetime.strptime(vencimiento_actual, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    fecha_vencimiento = (datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=duracion)).strftime("%Y-%m-%d")
                    
                    # ✅ USAR cursor_interna y conn_interna
                    cursor_interna.execute("""
                        INSERT INTO membresias (cliente_id, tipo_membresia, fecha_inicio, fecha_vencimiento, precio, estado)
                        VALUES (?, ?, ?, ?, ?, 'activa')
                    """, (cliente_id, tipo, fecha_inicio, fecha_vencimiento, precio))
                    
                    # Si había membresía activa, marcarla como renovada
                    if estado == 'activa':
                        cursor_interna.execute("""
                            UPDATE membresias SET estado = 'vencida' WHERE id = ?
                        """, (membresia_id,))
                    
                    conn_interna.commit()
                    
                    messagebox.showinfo("Éxito", 
                                    f"Membresía renovada correctamente\n"
                                    f"Cliente: {nombre_cliente}\n"
                                    f"Tipo: {tipo}\n"
                                    f"Inicio: {fecha_inicio}\n"
                                    f"Vencimiento: {fecha_vencimiento}\n"
                                    f"Precio: ${precio}")
                    
                    top.destroy()
                    
                except ValueError:
                    messagebox.showerror("Error", "Duración y precio deben ser números válidos")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo renovar la membresía: {str(e)}")
                finally:
                    # ✅ CERRAR CONEXIÓN INTERNA
                    if 'conn_interna' in locals():
                        conn_interna.close()
            
            # Botones
            btn_frame = tk.Frame(frame)
            btn_frame.pack(pady=10)
            
            btn_renovar = tk.Button(btn_frame, text="🔄 Renovar Membresía", 
                                command=procesar_renovacion,
                                bg='#27ae60', fg='white', font=('Arial', 11))
            btn_renovar.pack(side='left', padx=5)
            
            btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", 
                                command=top.destroy,
                                bg='#e74c3c', fg='white')
            btn_cancelar.pack(side='left', padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar la membresía: {str(e)}")
        finally:
            # ✅ CERRAR CONEXIÓN PRINCIPAL
            if 'conn' in locals():
                conn.close()

    def crear_ventana_modal(self, titulo, ancho, alto):
        """Crear una ventana modal que se mantiene encima de la principal"""
        top = tk.Toplevel(self.root)
        top.title(titulo)
        top.geometry(f"{ancho}x{alto}")
        top.resizable(False, False)
        
        # Configurar como ventana modal
        top.transient(self.root)
        top.grab_set()
        top.focus_force()
        
        # Centrar en la pantalla
        top.update_idletasks()
        x = (top.winfo_screenwidth() // 2) - (ancho // 2)
        y = (top.winfo_screenheight() // 2) - (alto // 2)
        top.geometry(f'{ancho}x{alto}+{x}+{y}')
        
        # Configurar comportamiento al cerrar
        def on_closing():
            top.grab_release()
            top.destroy()
        
        top.protocol("WM_DELETE_WINDOW", on_closing)
        
        # También cerrar modal con Escape
        top.bind('<Escape>', lambda e: on_closing())

        return top

    def reparacion_completa_clientes(self):
        """Reparación completa de la estructura de clientes"""
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            print("Iniciando reparación completa de la tabla clientes...")
            
            # 1. Verificar estructura
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = [col[1] for col in cursor.fetchall()]
            print(f"Columnas existentes: {columnas}")
            
            # 2. Agregar columna 'activo' si no existe
            if 'activo' not in columnas:
                cursor.execute("ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1")
                print("✓ Columna 'activo' agregada")
            
            # 3. Actualizar todos los registros existentes
            cursor.execute("UPDATE clientes SET activo = 1 WHERE activo IS NULL")
            print("✓ Registros existentes actualizados")
            
            # 4. Verificar que todo esté correcto
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE activo IS NULL")
            nulos = cursor.fetchone()[0]
            print(f"Clientes con activo nulo: {nulos}")
            
            conn.commit()
            print("✓ Reparación completada exitosamente")
            
            # 5. Recargar la vista
            if hasattr(self, 'tree_clientes'):
                self.cargar_clientes_en_treeview(self.tree_clientes)
                
        except Exception as e:
            print(f"Error en reparación: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def reparar_base_datos_clientes(self):
        """Reparar la base de datos para clientes existentes"""
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            print("🔧 Iniciando reparación de base de datos de clientes...")
            
            # 1. Verificar si la columna 'activo' existe
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'activo' not in columnas:
                # 2. Agregar columna 'activo' con valor por defecto 1
                cursor.execute("ALTER TABLE clientes ADD COLUMN activo INTEGER DEFAULT 1")
                print("✓ Columna 'activo' agregada a la tabla clientes")
            
            # 3. Asegurar que todos los clientes existentes tengan activo = 1
            cursor.execute("UPDATE clientes SET activo = 1 WHERE activo IS NULL")
            
            conn.commit()
            print("✓ Base de datos de clientes reparada exitosamente")
            
        except Exception as e:
            print(f"❌ Error reparando base de datos: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    # Llama a esta función al inicializar el módulo de clientes
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info
        self.reparar_base_datos_clientes()  # ✅ Reparar al iniciar
    
    def debug_treeview_data(self):
        """Función para depurar los datos del treeview"""
        print("=== DEBUG TREEVIEW DATA ===")
        for item in self.tree_clientes.get_children():
            valores = self.tree_clientes.item(item, 'values')
            print(f"Item: {item}, Valores: {valores}, Longitud: {len(valores)}")
        print("===========================")