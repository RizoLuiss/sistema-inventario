import tkinter as tk
from tkinter import ttk, messagebox, Canvas, Frame
from .clientes import ModuloClientes
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
import os
import sys
import hashlib

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso"""
    try:
        import sys
        import os
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class MainWindow:
    def __init__(self, root, user_info):
        self.root = root
        self.user_info = user_info

        #INICIALIZAR VARIABLES DE CACHE PARA ESTADÍSTICAS
        self.ultima_actualizacion_stats = None
        self.cache_tiempo = 30  # Cache de 30 segundos
        self.cache_stats = None  # (total_productos, stock_bajo, movimientos_hoy, total_clientes)

        # ESTABLECER ICONO PARA LA VENTANA PRINCIPAL
        try:
            self.root.iconbitmap(resource_path("assets/logo.ico"))
        except:
            try:
                logo_image = tk.PhotoImage(file=resource_path("assets/logo.png"))
                self.root.iconphoto(True, logo_image)
            except:
                pass

        self.root.title("Inventario 'Nombre' | club fitness")
        self.root.geometry("1000x800")


        #Inicializar módulo de clientes
        self.modulo_clientes = ModuloClientes(root, user_info)

        # Menú superior
        self.menu_bar = tk.Menu(root)
        
        # Menú Usuario
        menu_usuario = tk.Menu(self.menu_bar, tearoff=0)
        menu_usuario.add_command(label="Mi Perfil", command=self.mostrar_perfil)
        menu_usuario.add_separator()
        menu_usuario.add_command(label="Cerrar Sesión", command=self.cerrar_sesion)
        self.menu_bar.add_cascade(label=f"👤 {user_info['nombre']}", menu=menu_usuario)
        
        # Menú Administración (solo para admin)
        if user_info['rol'] == 'admin':
            menu_admin = tk.Menu(self.menu_bar, tearoff=0)
            menu_admin.add_command(label="Gestionar Usuarios", command=self.gestionar_usuarios)
            self.menu_bar.add_cascade(label="Administración", menu=menu_admin)
        
        self.root.config(menu=self.menu_bar)

        # Panel principal con pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña de Inicio/Dashboard
        self.tab_inicio = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inicio, text='Inicio')
        
        # Pestaña de Productos
        self.tab_productos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_productos, text='Productos')
        
        # Pestaña de Movimientos
        self.tab_movimientos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_movimientos, text='Movimientos')
        
        # Pestaña de Reportes
        self.tab_reportes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reportes, text='Reportes')

        # CONFIGURAR EVENTO AL CAMBIAR PESTAÑA
        self.notebook.bind("<<NotebookTabChanged>>", self.al_cambiar_pestaña)

        # Configurar cada pestaña
        self.configurar_tab_inicio()
        self.configurar_tab_productos()
        self.configurar_tab_movimientos()
        self.configurar_tab_reportes()
        #self.configurar_tab_usuarios()
        
        # Verificar stock bajo al inicio
        self.verificar_stock_bajo()
    
    def mostrar_perfil(self):
        """Mostrar información del perfil del usuario"""
        from tkinter import Toplevel, Label, Button
        
        top = Toplevel(self.root)
        top.title("Mi Perfil")
        top.geometry("300x200")
        top.resizable(False, False)
        
        info_text = f"""
        Usuario: {self.user_info['username']}
        Nombre: {self.user_info['nombre']}
        Rol: {self.user_info['rol']}
        """
        
        Label(top, text=info_text, justify='left', font=('Arial', 10)).pack(pady=20)
        Button(top, text="Cerrar", command=top.destroy).pack(pady=10)
    
    def cerrar_sesion(self):
        """Cerrar sesión y volver al login sin cerrar la aplicación"""
        if messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar sesión?"):
            # Ocultar la ventana principal en lugar de destruirla
            self.root.withdraw()  # Oculta la ventana principal
            
            # Crear nueva ventana de login
            from views.login import LoginWindow
            
            # Crear ventana de login temporal
            root_login = tk.Toplevel()
            root_login.title("Login - Sistema de Inventario")
            root_login.geometry("400x300")
            root_login.resizable(False, False)
            
            # Centrar la ventana de login
            window_width = 400
            window_height = 300
            screen_width = root_login.winfo_screenwidth()
            screen_height = root_login.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            root_login.geometry(f'{window_width}x{window_height}+{x}+{y}')
            
            # Configurar el protocolo de cierre para la ventana de login
            def on_closing_login():
                if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir del sistema?"):
                    root_login.destroy()
                    self.root.destroy()  # Cerrar completamente la aplicación
                else:
                    pass  # No hacer nada si cancela
            
            root_login.protocol("WM_DELETE_WINDOW", on_closing_login)
            
            # Crear la aplicación de login
            app_login = LoginWindow(root_login)
            
            # Función que se ejecutará cuando el login sea exitoso
            def on_login_success(user_info):
                # Destruir la ventana de login
                root_login.destroy()
                
                # Restaurar y actualizar la ventana principal
                self.root.deiconify()  # Mostrar la ventana principal
                self.user_info = user_info  # Actualizar info de usuario
                self.actualizar_interfaz_despues_login()  # Actualizar interfaz
            
            # Conectar el evento de login exitoso (necesitarás modificar LoginWindow)
            app_login.on_login_success = on_login_success
            
            # Enfocar la ventana de login
            root_login.focus_force()
            root_login.grab_set()

    def actualizar_interfaz_despues_login(self):
        """Actualizar la interfaz después de un nuevo login"""
        # Actualizar la barra de menú con el nuevo usuario
        self.menu_bar.destroy()
        self.configurar_menu()
        
         # ACTUALIZAR user_info en ModuloClientes
        if hasattr(self, 'modulo_clientes') and self.modulo_clientes is not None:
            self.modulo_clientes.user_info = self.user_info
        # Actualizar cualquier otra información que dependa del usuario
        self.verificar_stock_bajo()
        
        # Mostrar mensaje de bienvenida
        messagebox.showinfo("Bienvenido", f"¡Bienvenido {self.user_info['nombre']}!")
        
        # Regresar a la pestaña de inicio
        self.notebook.select(self.tab_inicio)

    def al_cambiar_pestaña(self, event):
        """Se ejecuta automáticamente cuando el usuario cambia de pestaña"""
        try:
            # Obtener el índice de la pestaña seleccionada
            pestaña_seleccionada = self.notebook.index(self.notebook.select())
            
            # Obtener el texto de la pestaña seleccionada
            texto_pestaña = self.notebook.tab(pestaña_seleccionada, "text")
            
            # print(f"Cambiando a pestaña: {texto_pestaña}")  # Para debug
            
            # Si la pestaña es "Inicio", actualizar estadísticas
            if texto_pestaña == "Inicio":
                self.actualizar_estadisticas()
                
        except Exception as e:
            print(f"Error al cambiar pestaña: {e}")
    
    def actualizar_estadisticas(self):
        """Actualizar las estadísticas en la pestaña de inicio"""
        try:
            ahora = datetime.now()
        
            # Verificar si necesitamos actualizar (cache de 30 segundos)
            if (self.ultima_actualizacion_stats and 
                (ahora - self.ultima_actualizacion_stats).seconds < self.cache_tiempo and
                self.cache_stats):
                
                # Usar datos cacheados
                total_productos, stock_bajo, movimientos_hoy, total_clientes = self.cache_stats
                cache_text = " (datos en cache)"
                
            else:
                # Obtener datos frescos
                total_productos, stock_bajo, movimientos_hoy, total_clientes = self.obtener_estadisticas()
                self.cache_stats = (total_productos, stock_bajo, movimientos_hoy, total_clientes)
                self.ultima_actualizacion_stats = ahora
                cache_text = ""
            
            stats_text = f"""
    • Total de productos: {total_productos}
    • Productos con stock bajo: {stock_bajo}
    • Movimientos hoy: {movimientos_hoy}
    • Clientes activos: {total_clientes}

     Actualizado: {datetime.now().strftime("%H:%M:%S")}"""
            
            # Actualizar el label de estadísticas
            if hasattr(self, 'label_stats'):
                self.label_stats.config(text=stats_text)
            else:
                # Si no existe el label, crearlo (por si acaso)
                self.label_stats = tk.Label(self.frame_stats, text=stats_text, 
                                        font=("Arial", 10), justify="left")
                self.label_stats.pack(padx=10, pady=10)
                
        except Exception as e:
            error_text = f"Error al cargar estadísticas: {str(e)}"
            if hasattr(self, 'label_stats'):
                self.label_stats.config(text=error_text)

    def configurar_menu(self):
        """Configurar la barra de menú con la información del usuario actual"""
        self.menu_bar = tk.Menu(self.root)
        
        # Menú Usuario
        menu_usuario = tk.Menu(self.menu_bar, tearoff=0)
        menu_usuario.add_command(label="Mi Perfil", command=self.mostrar_perfil)
        menu_usuario.add_separator()
        menu_usuario.add_command(label="Cerrar Sesión", command=self.cerrar_sesion)
        self.menu_bar.add_cascade(label=f"👤 {self.user_info['nombre']}", menu=menu_usuario)
        
        # Menú Administración (solo para admin)
        if self.user_info['rol'] == 'admin':
            menu_admin = tk.Menu(self.menu_bar, tearoff=0)
            menu_admin.add_command(label="Gestionar Usuarios", command=self.gestionar_usuarios)
            self.menu_bar.add_cascade(label="Administración", menu=menu_admin)
    
        self.root.config(menu=self.menu_bar)

    def gestionar_usuarios(self):
        """Ventana de gestión de usuarios (solo admin)"""
        from tkinter import Toplevel, Label, Entry, Button, StringVar, messagebox, Frame
        
        top = Toplevel(self.root)
        top.title("Gestión de Usuarios - Administrador")
        top.geometry("800x500")
        top.configure(bg='#f0f0f0')
        
        # Frame principal
        main_frame = Frame(top, bg='#f0f0f0', padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        Label(main_frame, text="GESTIÓN DE USUARIOS", 
            font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=(0, 15))
        
        # Frame para formulario de nuevo usuario
        form_frame = Frame(main_frame, bg='#f0f0f0', relief='solid', bd=1, padx=10, pady=10)
        form_frame.pack(fill='x', pady=(0, 15))
        
        Label(form_frame, text="Agregar Nuevo Usuario:", 
            font=('Arial', 10, 'bold'), bg='#f0f0f0').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Variables del formulario
        new_username = StringVar()
        new_password = StringVar()
        new_nombre = StringVar()
        new_rol = StringVar(value="usuario")
        
        # Campos del formulario
        Label(form_frame, text="Usuario:", bg='#f0f0f0').grid(row=1, column=0, sticky='w', pady=2)
        Entry(form_frame, textvariable=new_username, width=20).grid(row=1, column=1, pady=2, padx=(5, 0))
        
        Label(form_frame, text="Contraseña:", bg='#f0f0f0').grid(row=2, column=0, sticky='w', pady=2)
        Entry(form_frame, textvariable=new_password, show='•', width=20).grid(row=2, column=1, pady=2, padx=(5, 0))
        
        Label(form_frame, text="Nombre completo:", bg='#f0f0f0').grid(row=3, column=0, sticky='w', pady=2)
        Entry(form_frame, textvariable=new_nombre, width=20).grid(row=3, column=1, pady=2, padx=(5, 0))
        
        Label(form_frame, text="Rol:", bg='#f0f0f0').grid(row=4, column=0, sticky='w', pady=2)
        rol_frame = Frame(form_frame, bg='#f0f0f0')
        rol_frame.grid(row=4, column=1, sticky='w', pady=2, padx=(5, 0))
        
        from tkinter import ttk
        ttk.Radiobutton(rol_frame, text="Administrador", variable=new_rol, value="admin").pack(side='left')
        ttk.Radiobutton(rol_frame, text="Usuario", variable=new_rol, value="usuario").pack(side='left', padx=(10, 0))
        
        # Botón para agregar usuario
        def agregar_usuario():
            username = new_username.get().strip()
            password = new_password.get()
            nombre = new_nombre.get().strip()
            rol = new_rol.get()
            
            if not all([username, password, nombre]):
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            if len(password) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                # Verificar si el usuario ya existe
                cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
                if cursor.fetchone():
                    messagebox.showerror("Error", "El nombre de usuario ya existe")
                    return
                
                # Hash de la contraseña
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Insertar nuevo usuario
                cursor.execute(
                    "INSERT INTO usuarios (username, password_hash, nombre, rol) VALUES (?, ?, ?, ?)",
                    (username, password_hash, nombre, rol)
                )
                
                conn.commit()
                messagebox.showinfo("Éxito", "Usuario agregado correctamente")
                
                # Limpiar formulario
                new_username.set("")
                new_password.set("")
                new_nombre.set("")
                new_rol.set("usuario")
                
                # Actualizar lista de usuarios
                cargar_usuarios()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el usuario: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        Button(form_frame, text="Agregar Usuario", command=agregar_usuario,
            bg='#27ae60', fg='white').grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Frame para la lista de usuarios
        list_frame = Frame(main_frame, bg='#f0f0f0')
        list_frame.pack(fill='both', expand=True)
        
        # Treeview para usuarios
        columns = ("id", "username", "nombre", "rol")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        tree.heading("id", text="ID")
        tree.heading("username", text="Usuario")
        tree.heading("nombre", text="Nombre")
        tree.heading("rol", text="Rol")
        
        tree.column("id", width=50, anchor="center")
        tree.column("username", width=100)
        tree.column("nombre", width=150)
        tree.column("rol", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True)
        
        # Función para cargar usuarios
        def cargar_usuarios():
            for item in tree.get_children():
                tree.delete(item)
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, nombre, rol FROM usuarios WHERE activo = 1 ORDER BY username")
                
                for usuario in cursor.fetchall():
                    tree.insert("", "end", values=usuario)
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar los usuarios: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Función para eliminar usuario
        def eliminar_usuario():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione un usuario primero")
                return
            
            usuario_id = tree.item(seleccion[0])['values'][0]
            usuario_nombre = tree.item(seleccion[0])['values'][1]
            
            # No permitir eliminar al propio administrador
            if usuario_id == self.user_info['id']:
                messagebox.showerror("Error", "No puede eliminarse a sí mismo")
                return
            
            # No permitir eliminar el último admin
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND activo = 1")
                admin_count = cursor.fetchone()[0]
                
                if admin_count <= 1 and tree.item(seleccion[0])['values'][3] == 'admin':
                    messagebox.showerror("Error", "No puede eliminar el único administrador del sistema")
                    return
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al verificar administradores: {str(e)}")
                return
            finally:
                if 'conn' in locals():
                    conn.close()
            
            if messagebox.askyesno("Confirmar Eliminación", 
                                f"¿Está seguro de eliminar al usuario '{usuario_nombre}'?\n\n"
                                "Esta acción marcará al usuario como inactivo pero no borrará sus registros históricos."):
                try:
                    conn = sqlite3.connect("data/inventario.db")
                    cursor = conn.cursor()
                    
                    # Eliminación lógica (marcar como inactivo)
                    cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (usuario_id,))
                    conn.commit()
                    
                    messagebox.showinfo("Éxito", f"Usuario '{usuario_nombre}' eliminado correctamente")
                    cargar_usuarios()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar el usuario: {str(e)}")
                finally:
                    if 'conn' in locals():
                        conn.close()
        
        # Frame para botones de acción
        action_frame = Frame(list_frame, bg='#f0f0f0')
        action_frame.pack(fill='x', pady=(10, 0))
        
        # Botón para eliminar usuario
        btn_eliminar = Button(action_frame, text="Eliminar Usuario Seleccionado", 
                            command=eliminar_usuario, bg='#e74c3c', fg='white')
        btn_eliminar.pack(side='left', padx=5)
        
        # Botón para recargar lista
        btn_recargar = Button(action_frame, text="Actualizar Lista", 
                            command=cargar_usuarios, bg='#3498db', fg='white')
        btn_recargar.pack(side='left', padx=5)
        
        # Botón para cerrar
        btn_cerrar = Button(action_frame, text="Cerrar", 
                        command=top.destroy, bg='#95a5a6', fg='white')
        btn_cerrar.pack(side='right', padx=5)
        
        # Cargar usuarios al abrir la ventana
        cargar_usuarios()
        
        # Centrar la ventana
        top.transient(self.root)
        top.grab_set()
        top.focus_force()

    def configurar_tab_inicio(self):
        # Título de bienvenida
        label_bienvenida = tk.Label(self.tab_inicio, text="Sistema de Inventario - 'Nombre' | club fitness", 
                                font=("Arial", 16, "bold"))
        label_bienvenida.pack(pady=20)
        
        # Frame para estadísticas rápidas
        self.frame_stats = tk.LabelFrame(self.tab_inicio, text="Estadísticas Rápidas", font=("Arial", 12))
        self.frame_stats.pack(fill="x", padx=20, pady=10)
        
        # Label para estadísticas (GUARDAR REFERENCIA)
        self.label_stats = tk.Label(self.frame_stats, text="Cargando estadísticas...", 
                                font=("Arial", 10), justify="left")
        self.label_stats.pack(padx=10, pady=10)
        
        # Frame para accesos rápidos
        frame_accesos = tk.LabelFrame(self.tab_inicio, text="Accesos Rápidas", font=("Arial", 12))
        frame_accesos.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Botones de acceso rápido
        btn_frame = tk.Frame(frame_accesos)
        btn_frame.pack(expand=True)
        
        #Gestión de Clientes (fila 3, columna 0)
        btn_clientes = tk.Button(btn_frame, text="Gestión de Clientes", 
                                command=self.modulo_clientes.abrir_gestion_clientes,
                                width=20, height=3, bg="#610418", fg='white', 
                                font=("Arial", 10, "bold"))
        btn_clientes.grid(row=3, column=0, padx=10, pady=10)
        
        #Registrar Entrada Rápida (fila 3, columna 1)
        btn_entrada_rapida = tk.Button(btn_frame, text="Entrada Rápida", 
                                    command=self.abrir_entrada_rapida,
                                    width=20, height=3, bg="#03416a", fg='white', 
                                    font=("Arial", 10, "bold"))
        btn_entrada_rapida.grid(row=3, column=1, padx=10, pady=10)

        #Botóon gestion de membresias
        btn_membresias = tk.Button(btn_frame, text="Gestión de Membresías", 
                                command=self.modulo_clientes.abrir_gestion_membresias,
                                width=20, height=3, bg="#161615", fg='white', 
                                font=("Arial", 10, "bold"))
        btn_membresias.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        
        # Botón para agregar producto (fila 0, columna 0)
        btn_agregar = tk.Button(btn_frame, text="Agregar Producto", command=self.abrir_agregar_producto,
                            width=20, height=3, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_agregar.grid(row=0, column=0, padx=10, pady=10)
        
        # Botón para listar productos (fila 0, columna 1)
        btn_listar = tk.Button(btn_frame, text="Listar Productos", command=self.abrir_listar_productos,
                            width=20, height=3, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        btn_listar.grid(row=0, column=1, padx=10, pady=10)
        
        # Botón para registrar entrada (fila 1, columna 0)
        btn_entrada = tk.Button(btn_frame, text="Registrar Entrada", command=self.abrir_registrar_entrada,
                            width=20, height=3, bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
        btn_entrada.grid(row=1, column=0, padx=10, pady=10)
        
        # Botón para registrar salida (fila 1, columna 1)
        btn_salida = tk.Button(btn_frame, text="Registrar Salida", command=self.abrir_registrar_salida,
                            width=20, height=3, bg="#F44336", fg="white", font=("Arial", 10, "bold"))
        btn_salida.grid(row=1, column=1, padx=10, pady=10)
        
        # Botón para ver reportes (fila 2, column=0)
        btn_reportes = tk.Button(btn_frame, text="Generar Reporte", command=self.generar_reporte_stock,
                                width=20, height=3, bg="#9C27B0", fg="white", font=("Arial", 10, "bold"))
        btn_reportes.grid(row=2, column=0, padx=10, pady=10)
        
        # Botón para ver historial (fila 2, column=1)
        btn_historial = tk.Button(btn_frame, text="Ver Historial", command=self.abrir_historial_movimientos,
                                width=20, height=3, bg="#607D8B", fg="white", font=("Arial", 10, "bold"))
        btn_historial.grid(row=2, column=1, padx=10, pady=10)

        # Cargar estadísticas iniciales
        self.actualizar_estadisticas()
    
    def obtener_estadisticas(self):
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Total de productos
            cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = cursor.fetchone()[0]
            
            # Productos con stock bajo
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock <= minimo_stock")
            stock_bajo = cursor.fetchone()[0]
            
            # Movimientos hoy
            cursor.execute("SELECT COUNT(*) FROM movimientos WHERE date(fecha) = date('now')")
            movimientos_hoy = cursor.fetchone()[0]
            
            # Total de clientes activos
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1")
            total_clientes = cursor.fetchone()[0]
            
            return total_productos, stock_bajo, movimientos_hoy, total_clientes
            
        except Exception as e:
            print(f"Error al obtener estadísticas: {str(e)}")
            return 0, 0, 0, 0  # ✅ Asegúrate de devolver 4 valores
        finally:
            if 'conn' in locals():
                conn.close()
    
    def configurar_tab_productos(self):
        # Frame principal
        main_frame = tk.Frame(self.tab_productos)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Botones de acción
        btn_agregar = tk.Button(button_frame, text="Agregar Producto", command=self.abrir_agregar_producto,
                               bg="#4CAF50", fg="white")
        btn_agregar.pack(side="left", padx=5)
        
        btn_editar = tk.Button(button_frame, text="Editar Producto", 
                              command=lambda: self.editar_seleccionado(self.tree_productos),
                              bg="#FFC107")
        btn_editar.pack(side="left", padx=5)
        
        btn_eliminar = tk.Button(button_frame, text="Eliminar Producto",
                                command=lambda: self.eliminar_producto(self.tree_productos.item(self.tree_productos.focus())['values'][0]),
                                bg="#F44336", fg="white")
        btn_eliminar.pack(side="left", padx=5)
        
        # Frame de búsqueda
        search_frame = tk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(search_frame, text="Buscar:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        btn_buscar = tk.Button(search_frame, text="Buscar", command=self.actualizar_busqueda_productos)
        btn_buscar.pack(side="left", padx=5)
        
        # Treeview para productos
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Configuración del Treeview
        self.tree_productos = ttk.Treeview(tree_frame, columns=("1", "2", "3", "4", "5"), show="headings")
        
        # Configurar encabezados
        self.tree_productos.heading("1", text="ID")
        self.tree_productos.heading("2", text="Nombre")
        self.tree_productos.heading("3", text="Código Barras")
        self.tree_productos.heading("4", text="Stock")
        self.tree_productos.heading("5", text="Precio ($)")
        
        # Ajustar anchos de columnas
        self.tree_productos.column("1", width=50, anchor="center")
        self.tree_productos.column("2", width=200)
        self.tree_productos.column("3", width=150)
        self.tree_productos.column("4", width=80, anchor="center")
        self.tree_productos.column("5", width=100, anchor="e")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_productos.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_productos.configure(yscrollcommand=scrollbar.set)
        self.tree_productos.pack(fill="both", expand=True)
        
        # Cargar datos iniciales
        self.cargar_productos()
        
        # Enlazar evento de búsqueda
        self.search_var.trace("w", lambda name, index, mode: self.actualizar_busqueda_productos())
    
    def cargar_productos(self):
        # Limpiar treeview
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)
        
        # Cargar datos
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, codigo_barras, stock, precio FROM productos")
            
            for producto in cursor.fetchall():
                self.tree_productos.insert("", "end", values=producto)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def actualizar_busqueda_productos(self):
        query = self.search_var.get().lower()
        
        # Limpiar treeview
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)
        
        # Filtrar datos
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, codigo_barras, stock, precio FROM productos")
            
            for producto in cursor.fetchall():
                if query in str(producto).lower():
                    self.tree_productos.insert("", "end", values=producto)
                    
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def configurar_tab_movimientos(self):
        # Frame principal
        main_frame = tk.Frame(self.tab_movimientos)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Botones de acción
        btn_entrada = tk.Button(button_frame, text="Registrar Entrada", command=self.abrir_registrar_entrada,
                               bg="#4CAF50", fg="white")
        btn_entrada.pack(side="left", padx=5)
        
        btn_salida = tk.Button(button_frame, text="Registrar Salida", command=self.abrir_registrar_salida,
                              bg="#F44336", fg="white")
        btn_salida.pack(side="left", padx=5)
        
        btn_historial = tk.Button(button_frame, text="Ver Historial Completo", command=self.abrir_historial_movimientos,
                                 bg="#2196F3", fg="white")
        btn_historial.pack(side="left", padx=5)
        
        # Botón para borrar historial (NUEVO)
        btn_borrar = tk.Button(button_frame, text="Borrar Historial", command=self.borrar_historial_movimientos,
                              bg="#FF9800", fg="white")
        btn_borrar.pack(side="left", padx=5)

        # Treeview para movimientos recientes
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Configuración del Treeview
        self.tree_movimientos = ttk.Treeview(tree_frame, columns=("1", "2", "3", "4"), show="headings")
        
        # Configurar encabezados
        self.tree_movimientos.heading("1", text="Fecha")
        self.tree_movimientos.heading("2", text="Producto")
        self.tree_movimientos.heading("3", text="Tipo")
        self.tree_movimientos.heading("4", text="Cantidad")
        
        # Ajustar anchos de columnas
        self.tree_movimientos.column("1", width=150)
        self.tree_movimientos.column("2", width=200, anchor="center")
        self.tree_movimientos.column("3", width=100, anchor="center")
        self.tree_movimientos.column("4", width=100, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_movimientos.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_movimientos.configure(yscrollcommand=scrollbar.set)
        self.tree_movimientos.pack(fill="both", expand=True)
        
        # Cargar movimientos recientes
        self.cargar_movimientos_recientes()
    
    def cargar_movimientos_recientes(self):
        """Cargar movimientos con stock resultante CORRECTO basado en stock REAL"""
        # Limpiar treeview
        for item in self.tree_movimientos.get_children():
            self.tree_movimientos.delete(item)
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # CONSULTA CORREGIDA - Usa el stock REAL, no el calculado
            cursor.execute("""
                SELECT 
                    m.fecha, 
                    p.nombre, 
                    m.tipo, 
                    m.cantidad,
                    p.stock as stock_actual  -- ← ¡STOCK REAL!
                FROM movimientos m
                JOIN productos p ON m.producto_id = p.id
                ORDER BY m.fecha DESC, m.id DESC
                LIMIT 20
            """)
            
            for movimiento in cursor.fetchall():
                self.tree_movimientos.insert("", "end", values=movimiento)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los movimientos: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def diagnosticar_movimiento_erroneo(self):
        """Diagnóstico que muestra stock REAL vs stock CALCULADO"""
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            print("🔍 DIAGNÓSTICO COMPARATIVO:")
            print("=" * 70)
            print("ID | Fecha | Tipo | Cantidad | Stock Calc. | Stock Real | Diferencia")
            print("-" * 70)
            
            # 1. Obtener todos los movimientos en orden
            cursor.execute("""
                SELECT m.id, m.fecha, p.nombre, m.tipo, m.cantidad, m.producto_id
                FROM movimientos m
                JOIN productos p ON m.producto_id = p.id
                ORDER BY m.fecha, m.id
            """)
            
            movimientos = cursor.fetchall()
            
            for mov in movimientos:
                mov_id, fecha, nombre, tipo, cantidad, producto_id = mov
                
                # 2. Stock CALCULADO (como lo hace actualmente)
                cursor.execute("""
                    SELECT SUM(
                        CASE 
                            WHEN m2.tipo = 'entrada' THEN m2.cantidad 
                            ELSE -m2.cantidad 
                        END
                    ) 
                    FROM movimientos m2 
                    WHERE m2.producto_id = ? 
                    AND (m2.fecha < ? OR (m2.fecha = ? AND m2.id <= ?))
                """, (producto_id, fecha, fecha, mov_id))
                
                stock_calculado = cursor.fetchone()[0] or 0
                
                # 3. Stock REAL (de la tabla productos)
                cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
                stock_real = cursor.fetchone()[0]
                
                # 4. Diferencia
                diferencia = stock_real - stock_calculado
                
                print(f"{mov_id:3d} | {fecha} | {tipo:7s} | {cantidad:8d} | {stock_calculado:10d} | {stock_real:9d} | {diferencia:10d}")
                
                if diferencia != 0:
                    print(f"❌ INCONSISTENCIA: {diferencia} unidades de diferencia")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"Error en diagnóstico: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def sincronizar_stocks(self):
        """Sincroniza el stock calculado con el stock real"""
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            print("🔄 Sincronizando stocks calculados con stocks reales...")
            
            # 1. Para cada producto, obtener stock REAL
            cursor.execute("SELECT id, stock FROM productos")
            productos = cursor.fetchall()
            
            for producto_id, stock_real in productos:
                print(f"Producto {producto_id}: Stock Real = {stock_real}")
                
                # 2. Obtener todos los movimientos de este producto
                cursor.execute("""
                    SELECT id, fecha, tipo, cantidad 
                    FROM movimientos 
                    WHERE producto_id = ? 
                    ORDER BY fecha, id
                """, (producto_id,))
                
                movimientos = cursor.fetchall()
                stock_calculado = 0
                
                # 3. Recalcular movimientos con base en el stock REAL inicial
                for mov_id, fecha, tipo, cantidad in movimientos:
                    if tipo == 'entrada':
                        stock_calculado += cantidad
                    else:
                        stock_calculado -= cantidad
                    
                    # 4. Verificar consistencia
                    if stock_calculado != stock_real:
                        print(f"   Mov {mov_id}: {tipo} {cantidad} → Calc: {stock_calculado} vs Real: {stock_real}")
                        
                        # 5. Si hay inconsistencia, ajustar este movimiento
                        if stock_calculado != stock_real:
                            # Calcular la diferencia
                            diferencia = stock_real - stock_calculado
                            
                            if tipo == 'entrada':
                                nueva_cantidad = cantidad + diferencia
                                print(f"   ✓ Ajustando: entrada {cantidad} → {nueva_cantidad}")
                            else:
                                nueva_cantidad = cantidad - diferencia
                                print(f"   ✓ Ajustando: salida {cantidad} → {nueva_cantidad}")
                            
                            # Actualizar movimiento
                            cursor.execute("UPDATE movimientos SET cantidad = ? WHERE id = ?", 
                                        (nueva_cantidad, mov_id))
                            
                            # Recalcular stock calculado con el valor ajustado
                            if tipo == 'entrada':
                                stock_calculado += diferencia
                            else:
                                stock_calculado -= diferencia
                
                print(f"   ✅ Producto {producto_id} sincronizado")
            
            conn.commit()
            print("🎉 Todos los stocks sincronizados correctamente")
            
            # Actualizar interfaz
            self.cargar_productos()
            self.cargar_movimientos_recientes()
            
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
    def configurar_tab_reportes(self):
        # Frame principal
        main_frame = tk.Frame(self.tab_reportes)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botón para generar reporte
        btn_generar = tk.Button(main_frame, text="Generar Reporte de Stock", command=self.generar_reporte_stock,
                               width=20, height=2, bg="#9C27B0", fg="white", font=("Arial", 12, "bold"))
        btn_generar.pack(pady=20)
        
        # Frame para productos con stock bajo
        frame_bajo_stock = tk.LabelFrame(main_frame, text="Productos con Stock Bajo", font=("Arial", 12))
        frame_bajo_stock.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview para productos con stock bajo
        tree_frame = tk.Frame(frame_bajo_stock)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configuración del Treeview
        self.tree_bajo_stock = ttk.Treeview(tree_frame, columns=("1", "2", "3", "4"), show="headings")
        
        # Configurar encabezados
        self.tree_bajo_stock.heading("1", text="ID")
        self.tree_bajo_stock.heading("2", text="Nombre")
        self.tree_bajo_stock.heading("3", text="Stock Actual")
        self.tree_bajo_stock.heading("4", text="Stock Mínimo")
        
        # Ajustar anchos de columnas
        self.tree_bajo_stock.column("1", width=50, anchor="center")
        self.tree_bajo_stock.column("2", width=200)
        self.tree_bajo_stock.column("3", width=100, anchor="center")
        self.tree_bajo_stock.column("4", width=100, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_bajo_stock.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_bajo_stock.configure(yscrollcommand=scrollbar.set)
        self.tree_bajo_stock.pack(fill="both", expand=True)
        
        # Cargar productos con stock bajo
        self.cargar_productos_bajo_stock()
    
    def borrar_historial_movimientos(self):
        """Función para borrar el historial de movimientos con confirmación"""
        """Solo administradores pueden borrar historial"""
        if self.user_info['rol'] != 'admin':
            messagebox.showerror("Acceso denegado", "Solo los administradores pueden borrar el historial")
            return

        # Confirmación de seguridad
        respuesta = messagebox.askyesno(
            "Confirmar Borrado", 
            "¿Estás seguro de que quieres borrar TODO el historial de movimientos?\n\n"
            "Esta acción NO se puede deshacer y eliminará permanentemente "
            "todos los registros de entradas y salidas.\n\n"
            "Los stocks actuales de productos NO se verán afectados."
        )
        
        if not respuesta:
            return  # El usuario canceló la operación
        
        # Segunda confirmación por seguridad
        respuesta2 = messagebox.askyesno(
            "Confirmación Final", 
            "¿REALMENTE estás seguro?\n\n"
            "Esta acción eliminará permanentemente todos los registros históricos "
            "y no podrán ser recuperados."
        )
        
        if not respuesta2:
            return  # El usuario canceló en la segunda confirmación
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Borrar todos los movimientos
            cursor.execute("DELETE FROM movimientos")
            
            # Reiniciar el contador autoincremental (opcional, dependiendo de la necesidad)
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='movimientos'")
            
            conn.commit()
            
            messagebox.showinfo(
                "Éxito", 
                "Historial de movimientos borrado correctamente.\n\n"
                f"Se eliminaron todos los registros históricos."
            )
            
            # Actualizar la vista
            self.cargar_movimientos_recientes()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo borrar el historial: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def cargar_productos_bajo_stock(self):
        # Limpiar treeview
        for item in self.tree_bajo_stock.get_children():
            self.tree_bajo_stock.delete(item)
        
        # Cargar productos con stock bajo
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, stock, minimo_stock 
                FROM productos 
                WHERE stock <= minimo_stock
                ORDER BY stock ASC
            """)
            
            for producto in cursor.fetchall():
                self.tree_bajo_stock.insert("", "end", values=producto)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def verificar_stock_bajo(self):
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre, stock, minimo_stock 
                FROM productos 
                WHERE stock <= minimo_stock
            """)
        
            productos_bajos = cursor.fetchall()
        
            if productos_bajos:
                mensaje = "¡Stock bajo!\n\n"
                for producto in productos_bajos:
                    mensaje += f"- {producto[0]}: {producto[1]} (Mínimo: {producto[2]})\n"
            
                messagebox.showwarning("Alerta de Stock", mensaje)
    
        except Exception as e:
            print(f"Error al verificar stock: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def abrir_agregar_producto(self):
        """Ventana para agregar nuevos productos al inventario"""
        from tkinter import Toplevel, Label, Entry, Button, StringVar, DoubleVar, IntVar, messagebox
        
        # Configurar ventana emergente
        top = Toplevel(self.root)
        top.title("Agregar Nuevo Producto")
        top.geometry("500x400")
        
        # Variables TKinter
        nombre_var = StringVar()
        codigo_var = StringVar()
        precio_var = DoubleVar()
        stock_var = IntVar()
        stock_minimo_var = IntVar(value=5)
        
        # ✅ GUARDAR REFERENCIAS A LOS ENTRY
        self.entry_nombre = Entry(top, textvariable=nombre_var, width=40)
        self.entry_codigo = Entry(top, textvariable=codigo_var, width=40)
        self.entry_precio = Entry(top, textvariable=precio_var, width=40)  # ← GUARDAR REFERENCIA
        self.entry_stock = Entry(top, textvariable=stock_var, width=40)    # ← GUARDAR REFERENCIA
        self.entry_stock_minimo = Entry(top, textvariable=stock_minimo_var, width=40)  # ← GUARDAR REFERENCIA
        
        # Diseño del formulario
        Label(top, text="Nombre del Producto*:").pack(pady=(10, 0))
        self.entry_nombre.pack()
        
        Label(top, text="Código de Barras:").pack(pady=(10, 0))
        self.entry_codigo.pack()
        
        Label(top, text="Precio ($):").pack(pady=(10, 0))
        self.entry_precio.pack()  # ← USA LA REFERENCIA GUARDADA
        
        Label(top, text="Stock Inicial:").pack(pady=(10, 0))
        self.entry_stock.pack()  # ← USA LA REFERENCIA GUARDADA
        
        Label(top, text="Stock Mínimo:").pack(pady=(10, 0))
        self.entry_stock_minimo.pack()  # ← USA LA REFERENCIA GUARDADA
        
        Button(top, text="Guardar Producto", 
            command=self.guardar_producto,  # ← Ahora será método de clase
            bg="#4CAF50", fg="white").pack(pady=20)
        
        # Configurar enfoque inicial
        self.entry_nombre.focus_set()

    def guardar_producto(self):
        """Guardar producto con validaciones mejoradas"""
        try:
            # Validar nombre
            if not self.entry_nombre.get().strip():
                messagebox.showerror("Error", "El nombre del producto es obligatorio")
                self.entry_nombre.focus()
                return
            
            # ✅ VALIDACIÓN MEJORADA para precio
            es_valido, mensaje_error = self.validar_numero(self.entry_precio.get(), "precio", allow_zero=True)
            if not es_valido:
                messagebox.showerror("Error en Precio", mensaje_error)
                self.entry_precio.focus()
                self.entry_precio.select_range(0, tk.END)
                return
            
            # ✅ VALIDACIÓN MEJORADA para stock
            es_valido, mensaje_error = self.validar_numero(self.entry_stock.get(), "stock inicial", allow_zero=True)
            if not es_valido:
                messagebox.showerror("Error en Stock", mensaje_error)
                self.entry_stock.focus()
                self.entry_stock.select_range(0, tk.END)
                return
            
            # ✅ VALIDACIÓN MEJORADA para stock mínimo
            es_valido, mensaje_error = self.validar_numero(self.entry_stock_minimo.get(), "stock mínimo", allow_zero=True)
            if not es_valido:
                messagebox.showerror("Error en Stock Mínimo", mensaje_error)
                self.entry_stock_minimo.focus()
                self.entry_stock_minimo.select_range(0, tk.END)
                return
            
            # Si todas las validaciones pasan, guardar el producto
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO productos 
                (nombre, codigo_barras, precio, stock, minimo_stock) 
                VALUES (?, ?, ?, ?, ?)""",
                (
                    self.entry_nombre.get().strip(),
                    self.entry_codigo.get().strip() if self.entry_codigo.get().strip() else None,
                    float(self.entry_precio.get()),
                    int(self.entry_stock.get()),
                    int(self.entry_stock_minimo.get())
                )
            )
            
            conn.commit()
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
            
            # Actualizar las vistas
            self.cargar_productos()
            self.cargar_productos_bajo_stock()
            
            # Cerrar ventana
            self.entry_nombre.master.destroy()  # La ventana es el master del entry
        
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El código de barras ya existe")
            self.entry_codigo.focus()
            self.entry_codigo.select_range(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def generar_reporte_stock(self):
        """Genera un reporte PDF completo del inventario"""
        try:
            # Obtener datos de la base de datos
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            # Obtener todos los productos
            cursor.execute("""
                SELECT id, nombre, codigo_barras, stock, precio, minimo_stock 
                FROM productos 
                ORDER BY nombre
            """)
            productos = cursor.fetchall()
            
            # Obtener productos con stock bajo
            cursor.execute("""
                SELECT id, nombre, stock, minimo_stock 
                FROM productos 
                WHERE stock <= minimo_stock
                ORDER BY stock ASC
            """)
            productos_bajo_stock = cursor.fetchall()
            
            # Obtener estadísticas
            cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock <= minimo_stock")
            total_bajo_stock = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(stock * precio) FROM productos WHERE precio IS NOT NULL")
            valor_total = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Crear el documento PDF
            fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_archivo = f"reporte_inventario_{fecha}.pdf"
            
            doc = SimpleDocTemplate(nombre_archivo, pagesize=A4)
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.HexColor('#2C3E50')
            )
            
            # Título
            elements.append(Paragraph("REPORTE DE INVENTARIO - GIMNASIO 'NOMBRE'", title_style))
            elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Estadísticas generales
            stats_data = [
                ["Total de productos:", str(total_productos)],
                ["Productos con stock bajo:", str(total_bajo_stock)],
                ["Valor total del inventario:", f"${valor_total:,.2f}"]
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECF0F1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ]))
            
            elements.append(Paragraph("Estadísticas Generales", heading_style))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Tabla de todos los productos
            elements.append(Paragraph("Inventario Completo", heading_style))
            
            # Encabezados de la tabla
            headers = ["ID", "Nombre", "Código Barras", "Stock", "Mínimo", "Precio", "Estado"]
            
            # Datos de la tabla
            table_data = [headers]
            for producto in productos:
                id_prod, nombre, codigo, stock, precio, minimo = producto
                
                # Determinar estado
                if stock == 0:
                    estado = "AGOTADO"
                    color_estado = colors.red
                elif stock <= minimo:
                    estado = "BAJO STOCK"
                    color_estado = colors.orange
                else:
                    estado = "OK"
                    color_estado = colors.green
                
                # Formatear precio
                precio_str = f"${precio:,.2f}" if precio else "N/A"
                
                table_data.append([
                    str(id_prod), nombre, codigo or "N/A", 
                    str(stock), str(minimo), precio_str, estado
                ])
            
            # Crear tabla
            product_table = Table(table_data, repeatRows=1)
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                
                # Colorear filas según estado
                ('TEXTCOLOR', (6, 1), (6, -1), colors.black),
                ('BACKGROUND', (6, 1), (6, -1), colors.white),
                
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Centrar stock y mínimo
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),   # Alinear precios a la derecha
            ]))
            
            # Aplicar colores según el estado
            for i, row in enumerate(table_data[1:], 1):  # Saltar encabezados
                estado = row[6]
                if estado == "AGOTADO":
                    product_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (0, i), (-1, i), colors.red),
                        ('BACKGROUND', (6, i), (6, i), colors.red),
                        ('TEXTCOLOR', (6, i), (6, i), colors.white),
                    ]))
                elif estado == "BAJO STOCK":
                    product_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (0, i), (-1, i), colors.orange),
                        ('BACKGROUND', (6, i), (6, i), colors.orange),
                        ('TEXTCOLOR', (6, i), (6, i), colors.white),
                    ]))
            
            elements.append(product_table)
            elements.append(Spacer(1, 20))
            
            # Productos con stock bajo (si hay)
            if productos_bajo_stock:
                elements.append(Paragraph("Productos con Stock Bajo - ¡ATENCIÓN!", heading_style))
                
                alert_data = [["ID", "Nombre", "Stock Actual", "Stock Mínimo", "Déficit"]]
                
                for producto in productos_bajo_stock:
                    id_prod, nombre, stock, minimo = producto
                    deficit = minimo - stock
                    alert_data.append([str(id_prod), nombre, str(stock), str(minimo), str(deficit)])
                
                alert_table = Table(alert_data, repeatRows=1)
                alert_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFEBEE')),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.red),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    
                    ('GRID', (0, 0), (-1, -1), 1, colors.red),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ]))
                
                elements.append(alert_table)
                elements.append(Spacer(1, 20))
            
            # Pie de página con información adicional
            elements.append(Paragraph("Notas:", styles['Italic']))
            elements.append(Paragraph("- Este reporte fue generado automáticamente por el Sistema de Inventario 'Nombre'", styles['Italic']))
            elements.append(Paragraph("- Se recomienda revisar regularmente los productos con stock bajo", styles['Italic']))
            elements.append(Paragraph("- Los precios mostrados son por unidad", styles['Italic']))
            
            # Generar PDF
            doc.build(elements)
            
            # Abrir el archivo automáticamente si es posible
            try:
                os.startfile(nombre_archivo)  # Para Windows
            except:
                try:
                    os.system(f'open "{nombre_archivo}"')  # Para macOS
                except:
                    try:
                        os.system(f'xdg-open "{nombre_archivo}"')  # Para Linux
                    except:
                        pass
            
            messagebox.showinfo("Éxito", f"Reporte generado correctamente:\n{nombre_archivo}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {str(e)}")

    def abrir_listar_productos(self):
        # Cambiar a la pestaña de productos
        self.notebook.select(self.tab_productos)

    def editar_seleccionado(self, tree):
        """Método para editar producto seleccionado"""
        seleccionado = tree.focus()
        if seleccionado:
            producto_id = tree.item(seleccionado)['values'][0]
            self.abrir_editar_producto(producto_id)
        else:
            messagebox.showwarning("Advertencia", "Selecciona un producto primero")

    def abrir_registrar_entrada(self):
        """Ventana para registrar entrada de múltiples productos al inventario"""
        from tkinter import Toplevel, Label, Entry, Button, StringVar, messagebox, Frame, Scrollbar
    
        # Configurar ventana emergente
        top = Toplevel(self.root)
        top.title("Registrar Entrada de Productos")
        top.geometry("800x600")
        
        # Variables
        self.productos_entrada = []  # Lista para almacenar productos a registrar
        
        # Frame principal con scroll
        main_frame = Frame(top)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de búsqueda
        frame_busqueda = Frame(main_frame)
        frame_busqueda.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_busqueda, text="Buscar producto:").pack(anchor="w")
        
        busqueda_var = StringVar()
        entry_busqueda = Entry(frame_busqueda, textvariable=busqueda_var)
        entry_busqueda.pack(fill="x", pady=5)
        
        # Frame para resultados de búsqueda
        frame_resultados = Frame(main_frame)
        frame_resultados.pack(fill="x", pady=(0, 10))
        
        lista_productos = tk.Listbox(frame_resultados, height=4)
        lista_productos.pack(fill="x", pady=5)
        lista_productos.productos_info = {}
        
        # Frame para productos seleccionados (con scroll)
        frame_seleccionados = Frame(main_frame)
        frame_seleccionados.pack(fill="both", expand=True, pady=(0, 10))
        
        # Canvas y scrollbar para la tabla de productos seleccionados
        canvas_frame = Canvas(frame_seleccionados)
        scrollbar = Scrollbar(frame_seleccionados, orient="vertical", command=canvas_frame.yview)
        scrollable_frame = Frame(canvas_frame)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )
        
        canvas_frame.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_frame.configure(yscrollcommand=scrollbar.set)
        
        # Tabla para productos seleccionados
        headers = ["Producto", "Cantidad", "Acciones"]
        for i, header in enumerate(headers):
            label = Label(scrollable_frame, text=header, font=("Arial", 10, "bold"))
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        canvas_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame para botones
        frame_botones = Frame(main_frame)
        frame_botones.pack(fill="x", pady=(10, 0))
        
        # Función para buscar productos
        def buscar_productos():
            query = busqueda_var.get().lower()
            if not query:
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                # Buscar por código de barras o nombre
                cursor.execute("""
                    SELECT id, nombre, codigo_barras, stock 
                    FROM productos 
                    WHERE codigo_barras LIKE ? OR nombre LIKE ?
                """, (f"%{query}%", f"%{query}%"))
                
                productos = cursor.fetchall()
                
                # Limpiar lista
                lista_productos.delete(0, tk.END)
                lista_productos.productos_info = {}
                
                # Mostrar resultados
                for idx, producto in enumerate(productos):
                    lista_productos.insert(tk.END, f"{producto[1]} (Código: {producto[2]}, Stock: {producto[3]})")
                    lista_productos.productos_info[idx] = producto
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al buscar productos: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Función para agregar producto a la lista
        def agregar_producto():
            seleccion = lista_productos.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Selecciona un producto primero")
                return
            
            producto_info = lista_productos.productos_info[seleccion[0]]
            
            # Verificar si el producto ya está en la lista
            for prod in self.productos_entrada:
                if prod['id'] == producto_info[0]:
                    messagebox.showwarning("Advertencia", "Este producto ya está en la lista")
                    return
            
            # Crear ventana para ingresar cantidad
            def confirmar_cantidad():
                try:
                    cantidad = int(cantidad_var.get())
                    if cantidad <= 0:
                        messagebox.showerror("Error", "La cantidad debe ser mayor a cero")
                        return
                    
                    # Agregar producto a la lista
                    self.productos_entrada.append({
                        'id': producto_info[0],
                        'nombre': producto_info[1],
                        'codigo': producto_info[2],
                        'stock_actual': producto_info[3],
                        'cantidad': cantidad
                    })
                    
                    # Actualizar la tabla
                    actualizar_tabla()
                    top_cantidad.destroy()
                    
                except ValueError:
                    messagebox.showerror("Error", "La cantidad debe ser un número válido")
            
            top_cantidad = Toplevel(top)
            top_cantidad.title("Ingresar Cantidad")
            top_cantidad.geometry("300x150")
            
            cantidad_var = StringVar()
            
            Label(top_cantidad, text=f"Producto: {producto_info[1]}").pack(pady=5)
            Label(top_cantidad, text="Cantidad:").pack(pady=5)
            Entry(top_cantidad, textvariable=cantidad_var).pack(pady=5)
            Button(top_cantidad, text="Agregar", command=confirmar_cantidad).pack(pady=10)
        
        # Función para eliminar producto de la lista
        def eliminar_producto(index):
            if 0 <= index < len(self.productos_entrada):
                self.productos_entrada.pop(index)
                actualizar_tabla()
        
        # Función para actualizar la tabla de productos seleccionados
        def actualizar_tabla():
            # Limpiar tabla (excepto encabezados)
            for widget in scrollable_frame.grid_slaves():
                if int(widget.grid_info()["row"]) > 0:
                    widget.destroy()
            
            # Llenar tabla con productos
            for i, producto in enumerate(self.productos_entrada, 1):
                # Nombre del producto
                label_nombre = Label(scrollable_frame, text=producto['nombre'])
                label_nombre.grid(row=i, column=0, padx=5, pady=2, sticky="w")
                
                # Cantidad
                label_cantidad = Label(scrollable_frame, text=str(producto['cantidad']))
                label_cantidad.grid(row=i, column=1, padx=5, pady=2)
                
                # Botón eliminar
                btn_eliminar = Button(scrollable_frame, text="Eliminar", 
                                     command=lambda idx=i-1: eliminar_producto(idx))
                btn_eliminar.grid(row=i, column=2, padx=5, pady=2)
        
        # Función para registrar todas las entradas
        def registrar_entradas():
            if not self.productos_entrada:
                messagebox.showwarning("Advertencia", "No hay productos para registrar")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                for producto in self.productos_entrada:
                    # Registrar movimiento
                    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute("INSERT INTO movimientos (producto_id, tipo, cantidad, fecha) VALUES (?, 'entrada', ?, ?)",
                                (producto['id'], producto['cantidad'], fecha_hora))
                                        
                    # Actualizar stock
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", 
                                (producto['cantidad'], producto['id']))
                
                conn.commit()
                messagebox.showinfo("Éxito", f"Se registraron {len(self.productos_entrada)} entradas correctamente")
                
                # Actualizar las vistas
                self.cargar_productos()
                self.cargar_movimientos_recientes()
                self.cargar_productos_bajo_stock()
                
                top.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Botones
        btn_buscar = Button(frame_busqueda, text="Buscar", command=buscar_productos)
        btn_buscar.pack(pady=5)
        
        btn_agregar = Button(frame_resultados, text="Agregar Producto", command=agregar_producto)
        btn_agregar.pack(pady=5)
        
        btn_registrar = Button(frame_botones, text="Registrar Entradas", command=registrar_entradas,
                              bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_registrar.pack(side="right", padx=5)
        
        btn_cancelar = Button(frame_botones, text="Cancelar", command=top.destroy)
        btn_cancelar.pack(side="right", padx=5)
        
        # Enlazar Enter a la búsqueda
        entry_busqueda.bind("<Return>", lambda e: buscar_productos())

    def abrir_registrar_salida(self):
        """Ventana para registrar salida de múltiples productos del inventario"""
        from tkinter import Toplevel, Label, Entry, Button, StringVar, messagebox, Frame, Scrollbar
    
        # Configurar ventana emergente
        top = Toplevel(self.root)
        top.title("Registrar Salida de Productos")
        top.geometry("800x600")
        
        # Variables
        self.productos_salida = []  # Lista para almacenar productos a registrar
        
        # Frame principal con scroll
        main_frame = Frame(top)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame de búsqueda
        frame_busqueda = Frame(main_frame)
        frame_busqueda.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_busqueda, text="Buscar producto:").pack(anchor="w")
        
        busqueda_var = StringVar()
        entry_busqueda = Entry(frame_busqueda, textvariable=busqueda_var)
        entry_busqueda.pack(fill="x", pady=5)
        
        # Frame para resultados de búsqueda
        frame_resultados = Frame(main_frame)
        frame_resultados.pack(fill="x", pady=(0, 10))
        
        lista_productos = tk.Listbox(frame_resultados, height=4)
        lista_productos.pack(fill="x", pady=5)
        lista_productos.productos_info = {}
        
        # Frame para productos seleccionados (con scroll)
        frame_seleccionados = Frame(main_frame)
        frame_seleccionados.pack(fill="both", expand=True, pady=(0, 10))
        
        # Canvas y scrollbar para la tabla de productos seleccionados
        canvas_frame = Canvas(frame_seleccionados)
        scrollbar = Scrollbar(frame_seleccionados, orient="vertical", command=canvas_frame.yview)
        scrollable_frame = Frame(canvas_frame)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )
        
        canvas_frame.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_frame.configure(yscrollcommand=scrollbar.set)
        
        # Tabla para productos seleccionados
        headers = ["Producto", "Stock Actual", "Cantidad", "Acciones"]
        for i, header in enumerate(headers):
            label = Label(scrollable_frame, text=header, font=("Arial", 10, "bold"))
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        canvas_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame para botones
        frame_botones = Frame(main_frame)
        frame_botones.pack(fill="x", pady=(10, 0))
        
        # Función para buscar productos
        def buscar_productos():
            query = busqueda_var.get().lower()
            if not query:
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                # Buscar por código de barras o nombre
                cursor.execute("""
                    SELECT id, nombre, codigo_barras, stock 
                    FROM productos 
                    WHERE codigo_barras LIKE ? OR nombre LIKE ?
                """, (f"%{query}%", f"%{query}%"))
                
                productos = cursor.fetchall()
                
                # Limpiar lista
                lista_productos.delete(0, tk.END)
                lista_productos.productos_info = {}
                
                # Mostrar resultados
                for idx, producto in enumerate(productos):
                    lista_productos.insert(tk.END, f"{producto[1]} (Código: {producto[2]}, Stock: {producto[3]})")
                    lista_productos.productos_info[idx] = producto
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al buscar productos: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Función para agregar producto a la lista
        def agregar_producto():
            seleccion = lista_productos.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Selecciona un producto primero")
                return
            
            producto_info = lista_productos.productos_info[seleccion[0]]
            
            # Verificar si el producto ya está en la lista
            for prod in self.productos_salida:
                if prod['id'] == producto_info[0]:
                    messagebox.showwarning("Advertencia", "Este producto ya está en la lista")
                    return
            
            # Crear ventana para ingresar cantidad
            def confirmar_cantidad():
                try:
                    cantidad = int(cantidad_var.get())
                    if cantidad <= 0:
                        messagebox.showerror("Error", "La cantidad debe ser mayor a cero")
                        return
                    
                    # Verificar stock suficiente
                    if cantidad > producto_info[3]:
                        messagebox.showerror("Error", f"Stock insuficiente. Stock actual: {producto_info[3]}")
                        return
                    
                    # Agregar producto a la lista
                    self.productos_salida.append({
                        'id': producto_info[0],
                        'nombre': producto_info[1],
                        'codigo': producto_info[2],
                        'stock_actual': producto_info[3],
                        'cantidad': cantidad
                    })
                    
                    # Actualizar la tabla
                    actualizar_tabla()
                    top_cantidad.destroy()
                    
                except ValueError:
                    messagebox.showerror("Error", "La cantidad debe ser un número válido")
            
            top_cantidad = Toplevel(top)
            top_cantidad.title("Ingresar Cantidad")
            top_cantidad.geometry("400x250")
            
            cantidad_var = StringVar()
            
            Label(top_cantidad, text=f"Producto: {producto_info[1]}").pack(pady=5)
            Label(top_cantidad, text=f"Stock actual: {producto_info[3]}").pack(pady=5)
            Label(top_cantidad, text="Cantidad a retirar:").pack(pady=5)
            Entry(top_cantidad, textvariable=cantidad_var).pack(pady=5)
            Button(top_cantidad, text="Agregar", command=confirmar_cantidad).pack(pady=10)
        
        # Función para eliminar producto de la lista
        def eliminar_producto(index):
            if 0 <= index < len(self.productos_salida):
                self.productos_salida.pop(index)
                actualizar_tabla()
        
        # Función para actualizar la tabla de productos seleccionados
        def actualizar_tabla():
            # Limpiar tabla (excepto encabezados)
            for widget in scrollable_frame.grid_slaves():
                if int(widget.grid_info()["row"]) > 0:
                    widget.destroy()
            
            # Llenar tabla con productos
            for i, producto in enumerate(self.productos_salida, 1):
                # Nombre del producto
                label_nombre = Label(scrollable_frame, text=producto['nombre'])
                label_nombre.grid(row=i, column=0, padx=5, pady=2, sticky="w")
                
                # Stock actual
                label_stock = Label(scrollable_frame, text=str(producto['stock_actual']))
                label_stock.grid(row=i, column=1, padx=5, pady=2)
                
                # Cantidad
                label_cantidad = Label(scrollable_frame, text=str(producto['cantidad']))
                label_cantidad.grid(row=i, column=2, padx=5, pady=2)
                
                # Botón eliminar
                btn_eliminar = Button(scrollable_frame, text="Eliminar", 
                                     command=lambda idx=i-1: eliminar_producto(idx))
                btn_eliminar.grid(row=i, column=3, padx=5, pady=2)
        
        # Función para registrar todas las salidas
        def registrar_salidas():
            if not self.productos_salida:
                messagebox.showwarning("Advertencia", "No hay productos para registrar")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
                for producto in self.productos_salida:
                    # Registrar movimiento
                    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute("INSERT INTO movimientos (producto_id, tipo, cantidad, fecha) VALUES (?, 'salida', ?, ?)",
                                (producto['id'], producto['cantidad'], fecha_hora))
                    
                    # Actualizar stock
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", 
                                (producto['cantidad'], producto['id']))
                
                conn.commit()
                messagebox.showinfo("Éxito", f"Se registraron {len(self.productos_salida)} salidas correctamente")
                
                # Actualizar las vistas
                self.cargar_productos()
                self.cargar_movimientos_recientes()
                self.cargar_productos_bajo_stock()
                
                top.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Botones
        btn_buscar = Button(frame_busqueda, text="Buscar", command=buscar_productos)
        btn_buscar.pack(pady=5)
        
        btn_agregar = Button(frame_resultados, text="Agregar Producto", command=agregar_producto)
        btn_agregar.pack(pady=5)
        
        btn_registrar = Button(frame_botones, text="Registrar Salidas", command=registrar_salidas,
                              bg="#F44336", fg="white", font=("Arial", 10, "bold"))
        btn_registrar.pack(side="right", padx=5)
        
        btn_cancelar = Button(frame_botones, text="Cancelar", command=top.destroy)
        btn_cancelar.pack(side="right", padx=5)
        
        # Enlazar Enter a la búsqueda
        entry_busqueda.bind("<Return>", lambda e: buscar_productos())

    def abrir_editar_producto(self, producto_id=None):
        """Ventana para editar productos existentes"""
        from tkinter import Toplevel, Label, Entry, Button, StringVar, DoubleVar, IntVar, messagebox
        
        # Configurar ventana emergente
        top = Toplevel(self.root)
        top.title("Editar Producto")
        top.geometry("500x400")
        
        # Variables TKinter
        nombre_var = StringVar()
        codigo_var = StringVar()
        precio_var = DoubleVar()
        stock_var = IntVar()
        stock_minimo_var = IntVar()
        
        # Cargar datos del producto si se proporciona un ID
        def cargar_producto():
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, codigo_barras, precio, stock, minimo_stock FROM productos WHERE id = ?", (producto_id,))
                producto = cursor.fetchone()
            
                if producto:
                    nombre_var.set(producto[0])
                    codigo_var.set(producto[1] if producto[1] else "")
                    precio_var.set(producto[2] if producto[2] else 0.0)
                    stock_var.set(producto[3] if producto[3] else 0)
                    stock_minimo_var.set(producto[4] if producto[4] else 5)
                else:
                    messagebox.showerror("Error", "Producto no encontrado")
                    top.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar producto: {str(e)}")
                top.destroy()
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Función para guardar cambios
        def guardar_cambios():
            try:
                if not nombre_var.get():
                    messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
            
                cursor.execute(
                    """UPDATE productos SET 
                    nombre = ?,
                    codigo_barras = ?,
                    precio = ?,
                    stock = ?,
                    minimo_stock = ?
                    WHERE id = ?""",
                    (
                        nombre_var.get(),
                        codigo_var.get() if codigo_var.get() else None,
                        precio_var.get() if precio_var.get() > 0 else 0.0,
                        stock_var.get() if stock_var.get() > 0 else 0,
                        stock_minimo_var.get() if stock_minimo_var.get() > 0 else 5,
                        producto_id
                    )
                )
            
                conn.commit()
                messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                
                # Actualizar las vistas
                self.cargar_productos()
                self.cargar_productos_bajo_stock()
                
                top.destroy()
            
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El código de barras ya existe")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Diseño del formulario (similar a agregar producto)
        Label(top, text="Nombre del Producto*:").pack(pady=(10, 0))
        Entry(top, textvariable=nombre_var, width=40).pack()
        
        Label(top, text="Código de Barras:").pack(pady=(10, 0))
        Entry(top, textvariable=codigo_var, width=40).pack()
        
        Label(top, text="Precio ($):").pack(pady=(10, 0))
        Entry(top, textvariable=precio_var, width=40).pack()
        
        Label(top, text="Stock Actual:").pack(pady=(10, 0))
        Entry(top, textvariable=stock_var, width=40).pack()
        
        Label(top, text="Stock Mínimo:").pack(pady=(10, 0))
        Entry(top, textvariable=stock_minimo_var, width=40).pack()
        
        Button(top, text="Guardar Cambios", 
              command=guardar_cambios,
              bg="#2196F3", fg="white").pack(pady=20)
        
        # Cargar datos si hay un ID
        if producto_id:
            cargar_producto()

    def eliminar_producto(self, producto_id):
        """Eliminar un producto con confirmación"""
        from tkinter import messagebox
        
        # Confirmación
        if not messagebox.askyesno("Confirmar", "¿Eliminar este producto permanentemente?"):
            return
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
        
            # Eliminar producto
            cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
            conn.commit()
        
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
            
            # Actualizar las vistas
            self.cargar_productos()
            self.cargar_productos_bajo_stock()
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def abrir_historial_movimientos(self):
        """Mostrar historial completo de entradas/salidas con opción de borrado"""
        from tkinter import Toplevel, ttk
        
        top = Toplevel(self.root)
        top.title("Historial de Movimientos")
        top.geometry("1200x600")
        
        # Frame para botones
        button_frame = tk.Frame(top)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # Botón para borrar historial también en la ventana de historial completo
        btn_borrar = tk.Button(button_frame, text="Borrar Todo el Historial", 
                              command=self.borrar_historial_movimientos,
                              bg="#FF9800", fg="white")
        btn_borrar.pack(side="right", padx=5)
        
        # Treeview con scroll
        tree = ttk.Treeview(top, columns=("1", "2", "3", "4"), show="headings")
        tree.heading("1", text="Fecha")
        tree.heading("2", text="Producto")
        tree.heading("3", text="Tipo")
        tree.heading("4", text="Cantidad")
        
        # Ajustar columnas
        tree.column("1", width=150)
        tree.column("2", width=250)
        tree.column("3", width=100, anchor="center")
        tree.column("4", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Cargar datos
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.fecha, p.nombre, m.tipo, m.cantidad, 
                    (SELECT SUM(CASE WHEN m2.tipo = 'entrada' THEN m2.cantidad ELSE -m2.cantidad END)
                        FROM movimientos m2 
                        WHERE m2.producto_id = m.producto_id AND m2.fecha <= m.fecha) as stock
                FROM movimientos m
                JOIN productos p ON m.producto_id = p.id
                ORDER BY m.fecha DESC
            """)
            
            for movimiento in cursor.fetchall():
                tree.insert("", "end", values=movimiento)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def abrir_entrada_rapida(self):
        """Ventana super simple solo para registrar entrada de clientes"""
        top = tk.Toplevel(self.root)
        top.title("Entrada Rápida - 'Nombre' Gym")
        top.geometry("400x200")
        top.resizable(False, False)
        
        # Centrar la ventana
        top.transient(self.root)
        top.grab_set()
        
        frame = tk.Frame(top, padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Número de Cliente:", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        numero_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=numero_var, 
                        font=('Arial', 16), width=15, justify='center')
        entry.pack(pady=10)
        entry.focus()
        
        mensaje_label = tk.Label(frame, text="", font=('Arial', 10), fg='green')
        mensaje_label.pack(pady=5)
        
        def registrar():
            numero = numero_var.get().strip()
            if not numero:
                mensaje_label.config(text="Ingrese el número de cliente")
                return
            
            try:
                conn = sqlite3.connect("data/inventario.db")
                cursor = conn.cursor()
                
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
                    mensaje_label.config(text="❌ Cliente no encontrado")
                    return
                
                cliente_id, nombre, fecha_vencimiento, estado = cliente
                
                # Verificar membresía
                if not fecha_vencimiento or estado != 'activa':
                    mensaje_label.config(text="⚠️ Membresía vencida o inactiva")
                    return
                
                # Registrar entrada
                cursor.execute("""
                    INSERT INTO registros_entrada (cliente_id, usuario_id, fecha_entrada) 
                    VALUES (?, ?, ?)
                """, (cliente_id, self.user_info['id'], fecha_hora_actual))
                
                conn.commit()
                mensaje_label.config(text=f"✅ {nombre} - Entrada registrada")
                numero_var.set("")
                entry.focus()
                
            except Exception as e:
                mensaje_label.config(text=f"Error: {str(e)}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Enter para registrar
        entry.bind('<Return>', lambda e: registrar())
        
        btn_registrar = tk.Button(frame, text="Registrar Entrada", 
                                command=registrar,
                                bg='#27ae60', fg='white', font=('Arial', 12))
        btn_registrar.pack(pady=7)
        
        btn_cerrar = tk.Button(frame, text="Cerrar", 
                            command=top.destroy,
                            bg='#95a5a6', fg='white')
        btn_cerrar.pack(pady=5)

    def validar_numero(self, valor, nombre_campo, allow_zero=False):
        """Valida que un valor sea numérico y muestra mensaje de error personalizado"""
        try:
            # Intentar convertir a número
            numero = float(valor)
            
            # Validar si permite cero
            if not allow_zero and numero <= 0:
                return False, f"El {nombre_campo} debe ser mayor a cero"
            
            return True, None  # Válido, sin error
            
        except ValueError:
            return False, f"El {nombre_campo} debe ser un número válido\nNo se permiten letras ni símbolos"
    
#Ejemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()