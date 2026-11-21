"""Definición del menú lateral de TimberSoft.

Estructurado de acuerdo con el Análisis Orientado a Objetos y la matriz de roles:
- ADMIN: Acceso total a todos los módulos y reportes.
- EMPLEADO: Acceso limitado a Trabajos, Materiales y Clientes.
"""

MENU = [
    {
        'titulo': 'Ventas y Trabajos',
        'icono': '🪑',
        'permiso': 'gestionar_pedidos',
        'items': [
            {'titulo': 'Pedidos de taller', 'url': 'core:pedidos'},
            {'titulo': 'Presupuestos', 'url': 'core:presupuestos'},
        ],
    },
    {
        'titulo': 'Materiales',
        'icono': '🪵',
        'permiso': 'gestionar_inventario',
        'items': [
            {'titulo': 'Todos los materiales', 'url': 'core:materiales'},
            {'titulo': 'Stock crítico', 'url': 'core:materiales', 'query': '?stock=bajo'},
            {'titulo': 'Movimientos de stock', 'url': 'core:movimientos'},
            {'titulo': '+ Ajustar stock', 'url': 'core:movimiento_crear'},
        ],
    },
    {
        'titulo': 'Clientes',
        'icono': '👥',
        'permiso': 'gestionar_clientes',
        'items': [
            {'titulo': 'Listado de clientes', 'url': 'core:clientes'},
        ],
    },
    {
        'titulo': 'Compras',
        'icono': '🚚',
        'permiso': 'gestionar_compras',
        'items': [
            {'titulo': 'Compras realizadas', 'url': 'core:compras'},
            {'titulo': 'Proveedores', 'url': 'core:proveedores'},
        ],
    },
    {
        'titulo': 'Caja y Finanzas',
        'icono': '💵',
        'permiso': 'gestionar_caja',
        'items': [
            {'titulo': 'Cierre y movimientos de caja', 'url': 'core:caja'},
            {'titulo': '+ Registrar gasto operativo', 'url': 'core:gasto_crear'},
        ],
    },
    {
        'titulo': 'Reportes',
        'icono': '📊',
        'permiso': 'reportes_economicos',
        'items': [
            {'titulo': 'Centro de reportes y exportación', 'url': 'core:reportes'},
        ],
    },
    {
        'titulo': 'Auditoría',
        'icono': '🛡️',
        'permiso': 'respaldos_auditoria',
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
