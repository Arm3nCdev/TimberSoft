"""Definición del menú lateral de TimberSoft.

Estructurado de acuerdo con el Análisis Orientado a Objetos:
- Ventas y Trabajos: Pedidos y Presupuestos
- Materiales: Inventario, Stock crítico y Movimientos
- Compras: Compras a proveedores y Proveedores
- Clientes: Catálogo e historial de clientes
- Caja y Finanzas: Cierre diario y control de ingresos/egresos
- Auditoría: Registro automático de cambios
"""

MENU = [
    {
        'titulo': 'Ventas y Trabajos',
        'icono': '🪑',
        'items': [
            {'titulo': 'Pedidos', 'url': 'core:pedidos'},
            {'titulo': 'Presupuestos', 'url': 'core:presupuestos'},
        ],
    },
    {
        'titulo': 'Materiales',
        'icono': '🪵',
        'items': [
            {'titulo': 'Todos los materiales', 'url': 'core:materiales'},
            {'titulo': 'Stock crítico', 'url': 'core:materiales', 'query': '?stock=bajo'},
            {'titulo': 'Movimientos de stock', 'url': 'core:movimientos'},
        ],
    },
    {
        'titulo': 'Compras',
        'icono': '🚚',
        'items': [
            {'titulo': 'Compras realizadas', 'url': 'core:compras'},
            {'titulo': 'Proveedores', 'url': 'core:proveedores'},
        ],
    },
    {
        'titulo': 'Clientes',
        'icono': '👥',
        'items': [
            {'titulo': 'Listado de clientes', 'url': 'core:clientes'},
        ],
    },
    {
        'titulo': 'Caja y Finanzas',
        'icono': '💵',
        'items': [
            {'titulo': 'Cierre y movimientos de caja', 'url': 'core:caja'},
        ],
    },
    {
        'titulo': 'Auditoría',
        'icono': '🛡️',
        'items': [
            {'titulo': 'Registro de cambios', 'url': 'core:auditoria'},
        ],
    },
]


def titulo_por_slug(slug):
    for seccion in MENU:
        for item in seccion['items']:
            if item.get('slug') == slug:
                return seccion['titulo'], item['titulo']
    return None, None
