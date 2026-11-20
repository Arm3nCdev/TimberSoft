from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('presupuestos/', views.presupuestos, name='presupuestos'),
    path('presupuestos/nuevo/', views.nuevo_presupuesto, name='nuevo_presupuesto'),
    path('materiales/', views.materiales, name='materiales'),
    path('movimientos/', views.movimientos, name='movimientos'),
    path('compras/', views.compras, name='compras'),
    path('proveedores/', views.proveedores, name='proveedores'),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/nuevo/', views.cliente_nuevo, name='cliente_nuevo'),
    path('caja/', views.caja, name='caja'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('modulo/<slug:slug>/', views.modulo, name='modulo'),
]
