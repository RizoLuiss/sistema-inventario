import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os
import sys

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.on_login_success = None
        self.root.title("Login - Sistema de Inventario")
        self.root.geometry("400x300")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)
        
        # ESTABLECER ICONO PARA LA VENTANA DE LOGIN
        try:
            self.root.iconbitmap(resource_path("assets/logo.ico"))
        except:
            try:
                logo_image = tk.PhotoImage(file=resource_path("assets/logo.png"))
                self.root.iconphoto(True, logo_image)
            except:
                pass  # Si no hay logo, usar icono por defecto

        # Centrar la ventana
        window_width = 400
        window_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Marco principal
        main_frame = tk.Frame(root, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Logo o título
        title_label = tk.Label(main_frame, text="'Nombre' | club fitness", 
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(10, 5))
        
        subtitle_label = tk.Label(main_frame, text="Sistema de Inventario", 
                                 font=('Arial', 12), bg='#f0f0f0', fg='#7f8c8d')
        subtitle_label.pack(pady=(0, 30))
        
        # Marco del formulario
        form_frame = tk.Frame(main_frame, bg='#f0f0f0')
        form_frame.pack(fill='x', pady=10)
        
        # Usuario
        tk.Label(form_frame, text="Usuario:", bg='#f0f0f0', font=('Arial', 10), 
                fg='#34495e').grid(row=0, column=0, sticky='w', pady=8)
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=self.username_var, 
                                 font=('Arial', 10), width=25, relief='solid',
                                 bg='#ecf0f1', highlightthickness=1)
        username_entry.grid(row=0, column=1, pady=8, padx=(15, 0))
        
        # Contraseña
        tk.Label(form_frame, text="Contraseña:", bg='#f0f0f0', font=('Arial', 10),
                fg='#34495e').grid(row=1, column=0, sticky='w', pady=8)
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=self.password_var, 
                                 show='•', font=('Arial', 10), width=25, 
                                 relief='solid', bg='#ecf0f1', highlightthickness=1)
        password_entry.grid(row=1, column=1, pady=8, padx=(15, 0))
        
        # Botón de login
        login_btn = tk.Button(main_frame, text="Iniciar Sesión", 
                             command=self.verificar_login,
                             bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                             width=15, height=1, relief='flat', cursor='hand2')
        login_btn.pack(pady=20)
        
        # Credenciales por defecto (solo para desarrollo)
        demo_label = tk.Label(main_frame, 
                             text="Demo: admin / 123",
                             font=('Arial', 8), bg='#f0f0f0', fg='#95a5a6')
        demo_label.pack(pady=(5, 0))
        
        # Etiqueta de error
        self.error_label = tk.Label(main_frame, text="", fg='#e74c3c', bg='#f0f0f0',
                                   font=('Arial', 9))
        self.error_label.pack()
        
        # Enter para login
        username_entry.bind('<Return>', lambda e: self.verificar_login())
        password_entry.bind('<Return>', lambda e: self.verificar_login())
        
        # Focus en el primer campo
        username_entry.focus()
    
    def verificar_login(self, event=None):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username:
            self.error_label.config(text="Por favor, ingrese su usuario")
            return
        
        if not password:
            self.error_label.config(text="Por favor, ingrese su contraseña")
            return
        
        try:
            conn = sqlite3.connect("data/inventario.db")
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, password_hash, nombre, rol FROM usuarios WHERE username = ? AND activo = 1",
                (username,)
            )
            
            usuario = cursor.fetchone()
            
            if usuario and usuario[2] == hashlib.sha256(password.encode()).hexdigest():
                # Login exitoso
                user_info = {
                    'id': usuario[0],
                    'username': usuario[1],
                    'nombre': usuario[3],
                    'rol': usuario[4]
                }
                
                # Usar callback si está disponible
                if self.on_login_success:
                    self.on_login_success(user_info)
                else:
                    # Comportamiento original (para cuando se inicia desde main.py)
                    self.root.destroy()
                    from .main_window import MainWindow
                    root_main = tk.Tk()
                    app = MainWindow(root_main, user_info)
                    root_main.mainloop()
                
            else:
                self.error_label.config(text="Usuario o contraseña incorrectos")
                
        except sqlite3.Error as e:
            self.error_label.config(text=f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.error_label.config(text=f"Error inesperado: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()