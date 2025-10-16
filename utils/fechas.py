import sqlite3
# utils/fechas.py - VERSIÓN SIMPLIFICADA
from datetime import datetime

def obtener_fecha_hora_local():
    """Obtiene la fecha y hora actual del SISTEMA LOCAL"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_fecha_local():
    """Obtiene solo la fecha local (sin hora)"""
    return datetime.now().strftime("%Y-%m-%d")

def formatear_fecha_hora_legible(fecha_hora_str):
    """Convierte fecha/hora de la BD a formato legible"""
    try:
        # Intentar parsear diferentes formatos
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
            try:
                fecha_obj = datetime.strptime(fecha_hora_str, fmt)
                return fecha_obj.strftime("%d/%m/%Y %H:%M:%S")
            except:
                continue
        return fecha_hora_str  # Devolver original si no se puede parsear
    except:
        return fecha_hora_str