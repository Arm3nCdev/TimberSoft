# TimberSoft — Gestión para carpinterías

Sistema web en Django para la **Carpintería Fabmag** basado en el **Análisis Orientado a Objetos** y las **11 Reglas de Negocio** de `AGENTS.MD`.

- **Base de Datos**: Microsoft SQL Server (Base de datos: `TimberSoft`, driver: `ODBC Driver 18 for SQL Server`).
- **Monto y moneda**: Importes decimales en guaraníes (₲).
- **Herencia Persona**: `Cliente` y `Usuario` heredan de `Persona` compartiendo su `idPersona`.
- **Presupuestos y Pedidos**: Costeo detallado con materiales requeridos, mano de obra, flete según entrega y seña del 50%.
- **Inventario y Compras**: Movimientos de stock con entradas automáticas por compras y control de no negatividad.
- **Caja y Tesorería**: Registro de pagos, pagos a proveedores, gastos operativos y cierre de caja diario sin doble conteo.
- **Auditoría**: Trazabilidad automática de cambios (`RegistroCambio`) ante operaciones críticas.

## Cómo correrlo

```powershell
# 1. Instalar dependencias
.venv\Scripts\pip install -r requirements.txt

# 2. Aplicar migraciones en SQL Server
.venv\Scripts\python manage.py migrate

# 3. Cargar datos de demostración
.venv\Scripts\python manage.py cargar_demo

# 4. Iniciar el servidor web
.venv\Scripts\python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000**

### Usuarios demo creados por `cargar_demo`:
- **Administrador**: `admin` / `admin123` (Rol `ADMIN`)
- **Empleado**: `juan_taller` / `empleado123` (Rol `EMPLEADO`)
