from django.conf import settings
from django.urls import reverse

from .menu import MENU


def menu(request):
    """Arma el menú lateral resolviendo URLs y filtrando según el rol y permisos del usuario."""
    ruta_actual = request.get_full_path()
    secciones = []
    usuario = getattr(request, 'user', None)

    # Si no está autenticado, no exponer secciones protegidas en el menú lateral
    if not usuario or not usuario.is_authenticated:
        return {'menu_secciones': [], 'empresa': settings.EMPRESA}

    from .models import RolEnum
    es_empleado = hasattr(usuario, 'rol') and usuario.rol == RolEnum.EMPLEADO and not usuario.is_superuser

    for seccion in MENU:
        # Filtrado de secciones según la matriz de permisos de usuario (Sección 6 / Regla 11)
        permiso = seccion.get('permiso')
        if permiso and hasattr(usuario, 'validarPermiso'):
            if not usuario.validarPermiso(permiso):
                continue
        elif permiso and not usuario.is_superuser:
            continue

        items = []
        for item in seccion['items']:
            titulo_item = item['titulo']
            # Para el operario de taller, el movimiento de stock es registrar consumo
            if es_empleado and item.get('url') == 'core:movimiento_crear':
                titulo_item = '+ Registrar consumo'

            if 'url' in item:
                href = reverse(item['url']) + item.get('query', '')
            else:
                href = reverse('core:modulo', args=[item['slug']])
            items.append({'titulo': titulo_item, 'href': href, 'activo': href == ruta_actual})

        secciones.append({
            'titulo': seccion['titulo'],
            'icono': seccion['icono'],
            'items': items,
            'abierta': any(i['activo'] for i in items),
        })

    return {'menu_secciones': secciones, 'empresa': settings.EMPRESA}
