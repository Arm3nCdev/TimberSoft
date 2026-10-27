"""Definición del menú lateral.

Cada sección tiene un submenú desplegable. `url` es el nombre de una ruta
de Django; los módulos que todavía no existen apuntan a `core:modulo` con
un `slug` y muestran la pantalla de "en construcción".
"""

MENU = [
    {
        'titulo': 'Trabajos',
        'icono': '🪑',
        'items': [
            {'titulo': 'Nuevo presupuesto', 'slug': 'nuevo-presupuesto'},
            {'titulo': 'Órdenes de trabajo', 'slug': 'ordenes-trabajo'},
            {'titulo': 'Taller / producción', 'slug': 'produccion'},
            {'titulo': 'Agenda de entregas', 'slug': 'entregas'},
        ],
    },
    {
        'titulo': 'Materiales',
        'icono': '🪵',
        'items': [
            {'titulo': 'Todos los materiales', 'url': 'core:materiales'},
            {'titulo': 'Stock bajo', 'url': 'core:materiales', 'query': '?stock=bajo'},
            {'titulo': 'Categorías', 'slug': 'categorias'},
            {'titulo': 'Ajustes de stock', 'slug': 'ajustes-stock'},
            {'titulo': 'Calculadora de pies tablares', 'slug': 'calculadora-pt'},
        ],
    },
    {
        'titulo': 'Compras',
        'icono': '🚚',
        'items': [
            {'titulo': 'Órdenes de compra', 'slug': 'ordenes-compra'},
            {'titulo': 'Recepción de madera', 'slug': 'recepcion'},
            {'titulo': 'Proveedores y aserraderos', 'slug': 'proveedores'},
        ],
    },
    {
        'titulo': 'Clientes',
        'icono': '👥',
        'items': [
            {'titulo': 'Listado de clientes', 'slug': 'clientes'},
            {'titulo': 'Señas y saldos', 'slug': 'senas-saldos'},
            {'titulo': 'Cobranzas', 'slug': 'cobranzas'},
        ],
    },
    {
        'titulo': 'Caja',
        'icono': '💵',
        'items': [
            {'titulo': 'Facturación', 'slug': 'facturacion'},
            {'titulo': 'Apertura / cierre', 'slug': 'apertura-cierre'},
            {'titulo': 'Movimientos de caja', 'slug': 'movimientos-caja'},
        ],
    },
    {
        'titulo': 'Reportes',
        'icono': '📊',
        'items': [
            {'titulo': 'Libro IVA ventas', 'slug': 'libro-iva-ventas'},
            {'titulo': 'Libro IVA compras', 'slug': 'libro-iva-compras'},
            {'titulo': 'Rentabilidad por trabajo', 'slug': 'rentabilidad'},
            {'titulo': 'Valorización de stock', 'slug': 'valorizacion-stock'},
        ],
    },
    {
        'titulo': 'Configuración',
        'icono': '⚙️',
        'items': [
            {'titulo': 'Datos de la empresa', 'slug': 'empresa'},
            {'titulo': 'Timbrado y numeración', 'slug': 'timbrado'},
            {'titulo': 'Usuarios', 'slug': 'usuarios'},
        ],
    },
]


def titulo_por_slug(slug):
    for seccion in MENU:
        for item in seccion['items']:
            if item.get('slug') == slug:
                return seccion['titulo'], item['titulo']
    return None, None
