import sqlite3
from sqlite3 import Error
import hashlib
from datetime import datetime
import pytz

def crear_conexion():
    """Crear conexión a la base de datos SQLite con persistencia"""
    import sys
    import os
    
    # Determinar si estamos en ejecutable o desarrollo
    if getattr(sys, 'frozen', False):
        # Estamos en ejecutable
        base_path = os.path.dirname(sys.executable)
        db_path = os.path.join(base_path, "data", "inventario.db")
    else:
        # Estamos en desarrollo
        db_path = "data/inventario.db"
    
    # Crear carpeta data si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ Conexión exitosa a: {db_path}")
        return conn
    except Error as e:
        print(f"❌ Error al conectar a {db_path}: {e}")
    return conn

def hash_password(password):
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def obtener_hora_local_mexico():
    """Función centralizada para hora local"""
    try:
        # Intentar importar desde utils
        from utils.fechas import obtener_fecha_hora_local
        return obtener_fecha_hora_local()
    except ImportError:
        # Fallback si no existe utils
        from datetime import datetime, timedelta
        # Ajuste manual para México (UTC-6)
        utc_offset = -6
        hora_utc = datetime.utcnow()
        hora_local = hora_utc + timedelta(hours=utc_offset)
        return hora_local.strftime("%Y-%m-%d %H:%M:%S")

def fecha_actual_local():
    """Retorna la fecha actual en formato YYYY-MM-DD (hora local)"""
    return obtener_hora_local_mexico()[:10]

def inicializar_tablas():
    conn = crear_conexion()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Tabla productos (DEBE ir PRIMERO por la FOREIGN KEY)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    codigo_barras TEXT UNIQUE,
                    stock INTEGER DEFAULT 0,
                    precio REAL,
                    minimo_stock INTEGER DEFAULT 5
                )
            """)
            
            # Tabla movimientos (con verificación explícita)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'salida')),
                    cantidad INTEGER NOT NULL,
                    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            
            # Tabla usuarios 
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK (rol IN ('admin', 'usuario')),
                    activo INTEGER DEFAULT 1
                )
            """)

            # Insertar usuario admin por defecto si no existe
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
            if cursor.fetchone()[0] == 0:
                password_hash = hash_password("admin123")
                cursor.execute(
                    "INSERT INTO usuarios (username, password_hash, nombre, rol) VALUES (?, ?, ?, ?)",
                    ("admin", password_hash, "Administrador", "admin")
                )
                print("Usuario admin creado: admin / admin123")

            # Tabla de clientes (NUEVA)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_cliente TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
                    activo INTEGER DEFAULT 1
                )
            """)
            
            # Tabla de membresías (NUEVA)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS membresias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    tipo_membresia TEXT NOT NULL,
                    fecha_inicio TEXT NOT NULL,
                    fecha_vencimiento TEXT NOT NULL,
                    precio REAL NOT NULL,
                    estado TEXT DEFAULT 'activa' CHECK (estado IN ('activa', 'vencida', 'cancelada')),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            """)
            
            # Tabla de registros de entrada (NUEVA)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registros_entrada (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    fecha_entrada TEXT DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """)

            conn.commit()
            print("¡Tablas creadas correctamente!")
            
            # VERIFICACIÓN EXTRA
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            print("Tablas existentes:", cursor.fetchall())
            
        except Exception as e:
            print(f"Error crítico al crear tablas: {str(e)}")
            raise  # Relanza el error para no continuar con una DB corrupta
        finally:
            conn.close()

# Ejecutar al inicio para asegurar que la DB existe
inicializar_tablas()

def actualizar_tabla_registros():
    try:
        conn = sqlite3.connect("data/inventario.db")
        cursor = conn.cursor()
        
        # Verificar si la tabla vieja existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registros_entrada'")
        if cursor.fetchone():
            # Borrar tabla vieja (¡CUIDADO! Esto borra datos)
            cursor.execute("DROP TABLE registros_entrada")
            print("Tabla registros_entrada antigua eliminada")
        
        # Crear tabla nueva con estructura correcta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros_entrada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                fecha_entrada TEXT DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        conn.commit()
        print("Tabla registros_entrada creada con estructura correcta")
        
    except Exception as e:
        print(f"Error al actualizar tabla: {str(e)}")
    finally:
        if conn:
            conn.close()
