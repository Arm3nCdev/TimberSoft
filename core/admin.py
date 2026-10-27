from django.contrib import admin

from .models import Categoria, Cliente, Material, OrdenTrabajo


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ['nombre']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'categoria', 'unidad', 'precio_costo', 'stock', 'stock_minimo']
    list_filter = ['categoria', 'activo']
    search_fields = ['codigo', 'descripcion']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['razon_social', 'ruc', 'ciudad', 'telefono']
    search_fields = ['razon_social', 'ruc']


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'descripcion', 'estado', 'fecha_entrega', 'total', 'sena']
    list_filter = ['estado']
    search_fields = ['descripcion', 'cliente__razon_social']
