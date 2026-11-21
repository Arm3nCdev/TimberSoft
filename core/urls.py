from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Panel principal
    path('', views.dashboard, name='dashboard'),

    # Clientes (Fer: botón de agregar cliente y edición)
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),

    # Presupuestos (Melina: botón de agregar presupuesto y costeo detallado)
    path('presupuestos/', views.presupuestos, name='presupuestos'),
    path('presupuestos/nuevo/', views.presupuesto_crear, name='presupuesto_crear'),
    path('presupuestos/<int:pk>/', views.presupuesto_detalle, name='presupuesto_detalle'),
    path('presupuestos/<int:pk>/aprobar/', views.presupuesto_aprobar, name='presupuesto_aprobar'),
    path('presupuestos/<int:pk>/rechazar/', views.presupuesto_rechazar, name='presupuesto_rechazar'),
    path('presupuestos/<int:pk>/sena/', views.presupuesto_sena, name='presupuesto_sena'),

    # Pedidos
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pedidos/<int:pk>/estado/', views.pedido_actualizar_estado, name='pedido_actualizar_estado'),

    # Materiales e Inventario
    path('materiales/', views.materiales, name='materiales'),
    path('movimientos/', views.movimientos, name='movimientos'),
    path('movimientos/nuevo/', views.movimiento_crear, name='movimiento_crear'),

    # Compras y Proveedores
    path('compras/', views.compras, name='compras'),
    path('proveedores/', views.proveedores, name='proveedores'),

    # Caja y Finanzas
    path('caja/', views.caja, name='caja'),
    path('caja/cerrar/', views.caja_cerrar, name='caja_cerrar'),
    path('caja/gasto/nuevo/', views.gasto_crear, name='gasto_crear'),

    # Auditoría
    path('auditoria/', views.auditoria, name='auditoria'),

    # Reportes y Exportación
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/excel/<str:tipo>/', views.reporte_excel, name='reporte_excel'),
    path('reportes/imprimir/<str:tipo>/', views.reporte_imprimir, name='reporte_imprimir'),

    # Módulos genéricos
    path('modulo/<slug:slug>/', views.modulo, name='modulo'),
]
