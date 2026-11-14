# TimberSoft — Gestión para carpinterías

Sistema web en Django para la **Carpintería Fabmag**

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

