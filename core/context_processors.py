from django.conf import settings
from django.urls import reverse

from .menu import MENU


def menu(request):
    """Arma el menú lateral resolviendo URLs y marcando la opción activa."""
    ruta_actual = request.get_full_path()
    secciones = []
    for seccion in MENU:
        items = []
        for item in seccion['items']:
            if 'url' in item:
                href = reverse(item['url']) + item.get('query', '')
            else:
                href = reverse('core:modulo', args=[item['slug']])
            items.append({'titulo': item['titulo'], 'href': href, 'activo': href == ruta_actual})
        secciones.append({
            'titulo': seccion['titulo'],
            'icono': seccion['icono'],
            'items': items,
            'abierta': any(i['activo'] for i in items),
        })
    return {'menu_secciones': secciones, 'empresa': settings.EMPRESA}
