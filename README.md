# TimberSoft — Gestión para carpinterías

Sistema web en Django para la **Carpintería Fabmag** basado en el **Análisis Orientado a Objetos** y las **11 Reglas de Negocio** de `AGENTS.MD`.

- **Monto y moneda**: Importes decimales en guaraníes (₲).
- **Herencia Persona**: `Cliente` y `Usuario` heredan de `Persona` compartiendo su `idPersona`.
- **Presupuestos y Pedidos**: Flujo completo de costeo de materiales requeridos, mano de obra, flete según entrega (retiro en taller vs. domicilio), aprobación y seña (50%).
- **Inventario y Compras**: Movimientos de stock con entradas automáticas por compras y control de no negatividad.
- **Caja y Tesorería**: Registro de pagos, pagos a proveedores, gastos operativos y cierre de caja diario sin doble conteo.
- **Auditoría**: Trazabilidad automática de cambios (`RegistroCambio`) ante operaciones críticas.

## Cómo correrlo

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py cargar_demo        # carga datos y usuarios de prueba
.venv\Scripts\python manage.py test               # ejecuta las 11 pruebas de reglas de negocio
.venv\Scripts\python manage.py runserver
```

Abrir http://127.0.0.1:8000

### Usuarios demo creados por `cargar_demo`:
- **Administrador**: `admin` / `admin123` (Rol `ADMIN`)
- **Empleado**: `juan_taller` / `empleado123` (Rol `EMPLEADO`)

## Estructura del Modelo

- `core/models.py` — 21 clases (Persona, Cliente, Usuario, Proveedor, Material, Presupuesto, DetallePresupuesto, MaterialRequerido, Entrega, Adjunto, Pedido, Pago, GastoOperativo, Compra, DetalleCompra, PagoProveedor, MovimientoInventario, CierreCaja, PrecioProveedorMaterial, RegistroCambio, Respaldo) y 9 enumeraciones.
- `core/tests.py` — 11 pruebas unitarias automatizadas que garantizan el cumplimiento de las 11 reglas de negocio de `AGENTS.MD`.
- `core/views.py` — Dashboard filtrado por permisos según rol (Regla 11), catálogo de materiales y estado de stock.
- `core/admin.py` — Panel administrativo con inlines y auditoría en solo lectura.
