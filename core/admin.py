from django.contrib import admin
from .models import (
    Persona,
    Cliente,
    Usuario,
    Proveedor,
    Material,
    PrecioProveedorMaterial,
    Presupuesto,
    DetallePresupuesto,
    MaterialRequerido,
    Entrega,
    Adjunto,
    Pedido,
    Pago,
    GastoOperativo,
    CierreCaja,
    Compra,
    DetalleCompra,
    PagoProveedor,
    MovimientoInventario,
    RegistroCambio,
    Respaldo,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'obtenerNombreCompleto', 'rol', 'activo', 'is_staff']
    list_filter = ['rol', 'activo', 'is_staff']
    search_fields = ['username', 'nombre', 'apellido', 'ci']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['obtenerNombreCompleto', 'rucCliente', 'telefono', 'direccion', 'fechaRegistro']
    search_fields = ['nombre', 'apellido', 'rucCliente', 'ci']


class PrecioProveedorMaterialInline(admin.TabularInline):
    model = PrecioProveedorMaterial
    extra = 1


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['razonSocial', 'rucProveedor', 'rubroMaterial', 'telefono']
    search_fields = ['razonSocial', 'rucProveedor']
    inlines = [PrecioProveedorMaterialInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombreMaterial', 'unidadMedida', 'precioCosto', 'stockActual', 'stockMinimo', 'es_critico']
    list_filter = ['unidadMedida', 'activo']
    search_fields = ['codigo', 'nombreMaterial']

    @admin.display(boolean=True, description='Stock crítico')
    def es_critico(self, obj):
        return obj.esStockCritico()


class MaterialRequeridoInline(admin.TabularInline):
    model = MaterialRequerido
    extra = 1


@admin.register(DetallePresupuesto)
class DetallePresupuestoAdmin(admin.ModelAdmin):
    list_display = ['descripcionMueble', 'presupuesto', 'cantidad', 'subtotal']
    inlines = [MaterialRequeridoInline]


class DetallePresupuestoInline(admin.StackedInline):
    model = DetallePresupuesto
    extra = 1


class EntregaInline(admin.StackedInline):
    model = Entrega
    can_delete = False


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['idPresupuesto', 'cliente', 'fechaEmision', 'estadoPresupuesto', 'montoTotal', 'montoSena', 'saldoPendiente']
    list_filter = ['estadoPresupuesto', 'fechaEmision']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'cliente__rucCliente']
    inlines = [DetallePresupuestoInline, EntregaInline, PagoInline]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['idPedido', 'presupuesto', 'responsable', 'estadoPedido', 'fechaEntregaEstimada', 'saldo']
    list_filter = ['estadoPedido', 'responsable', 'fechaEntregaEstimada']
    search_fields = ['presupuesto__cliente__nombre', 'presupuesto__cliente__apellido', 'responsable__username']


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['idPago', 'presupuesto', 'tipoPago', 'medioPago', 'montoPago', 'fechaPago']
    list_filter = ['tipoPago', 'medioPago', 'fechaPago']
    search_fields = ['nroComprobante', 'presupuesto__cliente__nombre']


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1


class PagoProveedorInline(admin.TabularInline):
    model = PagoProveedor
    extra = 0


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['idCompra', 'proveedor', 'fechaCompra', 'total', 'saldoPendiente']
    list_filter = ['fechaCompra', 'proveedor']
    inlines = [DetalleCompraInline, PagoProveedorInline]


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['idMovimiento', 'fechaMovimiento', 'material', 'tipoMovimiento', 'cantidadMovimiento', 'motivoObservacion']
    list_filter = ['tipoMovimiento', 'fechaMovimiento']
    search_fields = ['material__nombreMaterial', 'motivoObservacion']


@admin.register(GastoOperativo)
class GastoOperativoAdmin(admin.ModelAdmin):
    list_display = ['idGasto', 'fechaGasto', 'conceptoGasto', 'montoGasto', 'comprobanteRef']
    list_filter = ['fechaGasto']
    search_fields = ['conceptoGasto', 'comprobanteRef']


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ['idCierre', 'fechaCierre', 'usuario', 'totalIngresos', 'totalEgresos', 'balanceNeto']
    list_filter = ['fechaCierre', 'usuario']


@admin.register(RegistroCambio)
class RegistroCambioAdmin(admin.ModelAdmin):
    list_display = ['idRegistro', 'fechaHora', 'entidad', 'idEntidad', 'accion', 'valorNuevo']
    list_filter = ['entidad', 'accion', 'fechaHora']
    readonly_fields = ['usuario', 'fechaHora', 'entidad', 'idEntidad', 'accion', 'valorAnterior', 'valorNuevo']


@admin.register(Respaldo)
class RespaldoAdmin(admin.ModelAdmin):
    list_display = ['idRespaldo', 'fechaHora', 'tamanoMB', 'estado', 'usuario']
    list_filter = ['estado', 'fechaHora']
