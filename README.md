# Sistema de Inventario - Gym

> **Sistema profesional de gestión integral** para gimnasios y centros deportivos  
> Desarrollado en **Python** | Interfaz **intuitiva** | Reportes **automáticos**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

---

## Características Principales

### Gestión de Inventario
- **Control completo** de productos y stock  
- **Entradas y salidas** con historial detallado  
- **Alertas automáticas** de stock bajo  
- **Códigos de barras** para identificación rápida  

### Sistema de Clientes
- **Gestión de membresías** (activas, vencidas, canceladas)  
- **Registro de entradas** en tiempo real  
- **Control de acceso** con validación automática  
- **Renovaciones y cortesías**  

### Punto de Venta
- **Ventas rápidas** con actualización automática de inventario  
- **Múltiples métodos de pago**  

### Reportes y Analytics
- **Reportes PDF** profesionales  
- **Estadísticas en tiempo real**  
- **Historial completo** de movimientos  
- **Dashboard** con métricas clave  

### Seguridad y Multi-usuario
- **Sistema de autenticación** con roles (Admin / Usuario)  
- **Hash SHA-256** para contraseñas  
- **Registro de actividades** por usuario  
- **Backup automático** de base de datos  

---

## Tecnologías Utilizadas

| Área | Tecnología |
|------|-------------|
| **Lenguaje** | Python 3.8+ |
| **Interfaz** | Tkinter / TTK |
| **Base de Datos** | SQLite3 |
| **Reportes** | ReportLab |
| **Seguridad** | Hashlib (SHA-256) |
| **Conectividad** | Serial / TCP-IP |

---

## ⚙️ Instalación y Uso

### Requisitos Previos
- Python 3.8 o superior  
- Pip (gestor de paquetes de Python)

### 🚀 Instalación Rápida
```bash
# 1. Clonar el repositorio
git clone https://github.com/RizoLuiss/sistema-inventario.git
cd sistema-inventario

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python main.py
```

### 🔑 Credenciales por Defecto
```
Usuario: admin  
Contraseña: admin123
```

---

## 🧩 Estructura del Proyecto

```
sistema-inventario/
├── main.py                # Punto de entrada principal
├── main_window.py         # Ventana principal y lógica central
├── login.py               # Sistema de autenticación
├── database.py            # Configuración y modelos de BD
├── clientes.py            # Módulo de gestión de clientes
├── utils/                 # Utilidades y helpers
│   ├── fechas.py          # Manejo de timezones y formatos
│   └── validaciones.py    # Validaciones de datos
├── data/                  # Base de datos (se crea automáticamente)
└── assets/                # Recursos gráficos
```

---

## 🏢 Para Empresas y Negocios

¿Necesita una **solución personalizada**?  
Este sistema base es open-source y gratuito, pero también ofrezco servicios profesionales para adaptarlo a su negocio:

### 💼 Servicios Profesionales
- Customizaciones a medida  
- Integración con sistemas existentes (contabilidad, ERP, etc.)  
- Desarrollo de apps móviles complementarias  
- Soporte técnico prioritario 24/7  
- Capacitación de personal  
- Hosting y mantenimiento administrado  

### 🌟 Características Premium Disponibles
- Múltiples sucursales con sincronización en tiempo real  
- App móvil para clientes y staff  
- Facturación electrónica integrada  
- Reportes avanzados con business intelligence  
- API REST para integraciones externas  
- Sistema de reservas de clases y espacios  
- Control de acceso biométrico  

📩 **Contacto comercial:**  
**Email:** [rizogutierrezluiss@gmail.com](mailto:rizogutierrezluiss@gmail.com)  
**LinkedIn:** [Mi Perfil Profesional](https://www.linkedin.com/in/luis-alberto-rizo-gutierrez-44b284360)  
**Portfolio:** [Ver Mi Trabajo](https://rizoluiss.github.io/)  
**GitHub:** [Mis Otros Proyectos](https://github.com/RizoLuiss)

---

## 🤝 Desarrollo y Contribución

¿Quieres **contribuir**? ¡Las aportaciones son bienvenidas!  
Este proyecto es ideal para:

- Estudiantes que quieran aprender desarrollo real  
- Desarrolladores que deseen mejorar sus habilidades en Python  
- Emprendedores que necesiten un sistema base para su negocio  

### 🧭 Guía de Contribución
1. Haz un **fork** del proyecto  
2. Crea una rama de feature  
   ```bash
   git checkout -b feature/nuevaCaracteristica
   ```
3. Realiza tus cambios y haz commit  
   ```bash
   git commit -m 'Agregar nueva característica'
   ```
4. Sube la rama  
   ```bash
   git push origin feature/nuevaCaracteristica
   ```
5. Abre un **Pull Request**

### 🐛 Reportar Issues
Si encuentras un bug o tienes sugerencias:
1. Revisa los issues existentes  
2. Crea uno nuevo con:  
   - Descripción detallada  
   - Pasos para reproducirlo  
   - Capturas de pantalla (si aplica)  

---

## 📈 Métricas del Proyecto
- +2,000 líneas de código Python  
- +15 módulos integrados  
- +20 funcionalidades principales  
- 💯 100% código desarrollado desde cero  

---

## 📄 Licencia
Este proyecto está bajo la **Licencia MIT** – consulta el archivo [LICENSE](LICENSE) para más detalles.  

¿Interesado en una **licencia comercial** o **desarrollo personalizado**?  
Contáctame para una consulta gratuita.

---

## ⭐ Apóyame
Si este proyecto te resultó útil:

- Dale una **estrella ⭐** en GitHub  
- Compártelo con otros desarrolladores o emprendedores  
- Sígueme para más proyectos  

---

**Desarrollado con ❤️ por [Luis Rizo](https://github.com/RizoLuiss)**  
*Full-Stack Developer & Python Enthusiast*
