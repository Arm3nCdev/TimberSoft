# TimberSoft — Gestión para carpinterías

Sistema web en Django (backend Python + plantillas Django) pensado para carpinterías de Paraguay: trabajos a pedido con seña y saldo,
maderas en pies tablares, tableros por placa, herrajes e insumos;:
montos en guaraníes (₲, sin decimales), IVA 10% / 5% / exenta incluido en el precio, RUC/CI de clientes
y numeración de facturas `001-001-0000001`.

## Cómo correrlo

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py cargar_demo        # datos de ejemplo
.venv\Scripts\python manage.py createsuperuser    # opcional, para /admin
.venv\Scripts\python manage.py runserver
```

Abrir http://127.0.0.1:8000

## Estructura

- `core/models.py` — Categoría, Material, Cliente, OrdenTrabajo
- `core/menu.py` — opciones del menú lateral y sus submenús
- `core/views.py` — Inicio (resumen del taller), Materiales, pantalla "en construcción"
- `core/templatetags/formato_py.py` — filtros `guaranies` y `cantidad` (formato 1.234.567)
- `core/templates/core/` — plantillas; `core/static/core/` — CSS y JS
