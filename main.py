from views.login import LoginWindow
import tkinter as tk
import os
import sys

from database import inicializar_tablas
inicializar_tablas()  # <- Esto creará las tablas si no existen

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    # Crear ventana de login
    root_login = tk.Tk()
    app_login = LoginWindow(root_login)
    root_login.mainloop()

if __name__ == "__main__":
    main()