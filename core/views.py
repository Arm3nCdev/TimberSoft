import csv
from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ClienteForm,
    PresupuestoCabeceraForm,
    EntregaForm,
    DetallePresupuestoForm,
    MovimientoInventarioForm,
    GastoOperativoForm,
    CambiarEstadoPedidoForm,
)
from .menu import titulo_por_slug
from .models import (
    Material,
    Pedido,
    Presupuesto,
    DetallePresupuesto,
    MaterialRequerido,
    Entrega,
    ModalidadEntrega,
    Cliente,
    Proveedor,
    Compra,
    MovimientoInventario,
    TipoMovimiento,
    GastoOperativo,
    PagoProveedor,
    Pago,
    TipoPago,
    MedioPago,
    CierreCaja,
    RegistroCambio,
    EstadoPedido,
    EstadoPresupuesto,
    RolEnum,
)


def requiere_permiso(permiso):
    """Verifica que el usuario esté autenticado y tenga el permiso especificado según la matriz de roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if not hasattr(request.user, 'validarPermiso') or not request.user.validarPermiso(permiso):
                messages.error(
                    request,
                    'Acceso denegado: Su rol de empleado no tiene permisos para acceder al módulo administrativo solicitado.'
                )
                return redirect('core:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# ==============================================================================
# 1. AUTENTICACIÓN
# ==============================================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '').strip()
        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.obtenerNombreCompleto() or user.username}!')
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Verifique sus credenciales.')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('core:login')


# ==============================================================================
# 2. PANEL PRINCIPAL (DASHBOARD)
# ==============================================================================

@login_required
def dashboard(request):
    hoy = timezone.localdate()

    # Regla 11: El EMPLEADO solo ve y actualiza los pedidos que tiene asignados; el ADMIN ve todos.
    if hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser:
        pedidos_base = Pedido.objects.filter(responsable=request.user)
        es_empleado = True
    else:
        pedidos_base = Pedido.objects.all()
        es_empleado = False

    abiertos = pedidos_base.exclude(estadoPedido=EstadoPedido.ENTREGADO)
    stock_bajo = Material.objects.filter(activo=True, stockActual__lte=F('stockMinimo'))
    saldo_total = sum((p.saldo for p in abiertos), Decimal('0.00')) if not es_empleado else Decimal('0.00')

    contexto = {
        'en_produccion': pedidos_base.filter(estadoPedido=EstadoPedido.EN_PROCESO).count(),
        'presupuestos': Presupuesto.objects.filter(estadoPresupuesto=EstadoPresupuesto.PENDIENTE).count(),
        'entregas_semana': pedidos_base.filter(
            fechaEntregaEstimada__range=(hoy, hoy + timedelta(days=7))
        ).exclude(estadoPedido=EstadoPedido.ENTREGADO).count(),
        'atrasados': pedidos_base.filter(fechaEntregaEstimada__lt=hoy).exclude(estadoPedido=EstadoPedido.ENTREGADO).count(),
        'saldo_cobrar': saldo_total,
        'proximas_entregas': abiertos.select_related('presupuesto__cliente', 'responsable').order_by('fechaEntregaEstimada')[:6],
        'stock_bajo': stock_bajo.order_by('nombreMaterial')[:6],
        'cantidad_stock_bajo': stock_bajo.count(),
        'es_empleado': es_empleado,
        'hoy': hoy,
    }
    return render(request, 'core/dashboard.html', contexto)


# ==============================================================================
# 3. CLIENTES (Fer: botón de agregar cliente y edición)
# ==============================================================================

@login_required
def clientes(request):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    q = request.GET.get('q', '').strip()
    qs = Cliente.objects.prefetch_related('presupuestos__pedido').order_by('apellido', 'nombre')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(rucCliente__icontains=q) | Q(ci__icontains=q))

    return render(request, 'core/clientes.html', {
        'clientes': qs,
        'q': q,
        'es_empleado': es_empleado,
    })


@login_required
def cliente_crear(request):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente «{cliente.obtenerNombreCompleto()}» registrado exitosamente.')
            return redirect('core:clientes')
    else:
        form = ClienteForm()

    return render(request, 'core/cliente_form.html', {'form': form, 'es_edicion': False, 'es_empleado': es_empleado})


@login_required
def cliente_editar(request, pk):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Datos de «{cliente.obtenerNombreCompleto()}» actualizados exitosamente.')
            return redirect('core:clientes')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'core/cliente_form.html', {'form': form, 'es_edicion': True, 'cliente': cliente, 'es_empleado': es_empleado})

    if form.is_valid():
        form.save()
        messages.success(request, f'Datos de «{cliente.obtenerNombreCompleto()}» actualizados exitosamente.')
        return redirect('core:clientes')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'core/cliente_form.html', {'form': form, 'es_edicion': True, 'cliente': cliente})


# ==============================================================================
# 4. PRESUPUESTOS (Melina: botón de agregar presupuesto y costeo detallado)
# ==============================================================================

@login_required
def presupuestos(request):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    qs = Presupuesto.objects.select_related('cliente', 'entrega').prefetch_related('detalles__materiales_requeridos', 'pagos')
    if estado:
        qs = qs.filter(estadoPresupuesto=estado)
    if q:
        qs = qs.filter(
            Q(cliente__nombre__icontains=q) |
            Q(cliente__apellido__icontains=q) |
            Q(cliente__rucCliente__icontains=q) |
            Q(detalles__descripcionMueble__icontains=q)
        ).distinct()

    return render(request, 'core/presupuestos.html', {
        'presupuestos': qs.order_by('-idPresupuesto'),
        'q': q,
        'estado_seleccionado': estado,
        'estados': EstadoPresupuesto.choices,
        'es_empleado': es_empleado,
    })


@login_required
def presupuesto_crear(request):
    if request.method == 'POST':
        pres_form = PresupuestoCabeceraForm(request.POST)
        entrega_form = EntregaForm(request.POST)
        det_form = DetallePresupuestoForm(request.POST)

        if pres_form.is_valid() and entrega_form.is_valid() and det_form.is_valid():
            pres = pres_form.save(commit=False)
            pres.estadoPresupuesto = EstadoPresupuesto.PENDIENTE
            pres.save()

            entrega = entrega_form.save(commit=False)
            entrega.presupuesto = pres
            entrega.save()

            detalle = det_form.save(commit=False)
            detalle.presupuesto = pres
            detalle.save()

            mat = det_form.cleaned_data.get('material')
            cant_mat = det_form.cleaned_data.get('cantidad_material')
            if mat and cant_mat:
                MaterialRequerido.objects.create(
                    detallePresupuesto=detalle,
                    material=mat,
                    cantidadRequerida=cant_mat
                )

            messages.success(request, f'Presupuesto #{pres.idPresupuesto:05d} generado correctamente.')
            return redirect('core:presupuesto_detalle', pk=pres.idPresupuesto)
    else:
        pres_form = PresupuestoCabeceraForm(initial={'fechaEmision': timezone.localdate(), 'costoManoObra': Decimal('1500000.00')})
        entrega_form = EntregaForm(initial={'modalidadEntrega': ModalidadEntrega.RETIRO_TALLER, 'costoFlete': Decimal('0.00')})
        det_form = DetallePresupuestoForm(initial={'cantidad': 1, 'margen': Decimal('500000.00')})

    return render(request, 'core/presupuesto_form.html', {
        'pres_form': pres_form,
        'entrega_form': entrega_form,
        'det_form': det_form,
    })


@login_required
def presupuesto_detalle(request, pk):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    pres = get_object_or_404(Presupuesto.objects.select_related('cliente', 'entrega', 'pedido').prefetch_related('detalles__materiales_requeridos__material', 'pagos'), pk=pk)
    return render(request, 'core/presupuesto_detalle.html', {'pres': pres, 'es_empleado': es_empleado})


@login_required
def presupuesto_aprobar(request, pk):
    pres = get_object_or_404(Presupuesto, pk=pk)
    pres.aprobar()
    messages.success(request, f'Presupuesto #{pres.idPresupuesto:05d} APROBADO.')
    return redirect('core:presupuesto_detalle', pk=pres.idPresupuesto)


@login_required
def presupuesto_rechazar(request, pk):
    pres = get_object_or_404(Presupuesto, pk=pk)
    pres.rechazar()
    messages.warning(request, f'Presupuesto #{pres.idPresupuesto:05d} RECHAZADO.')
    return redirect('core:presupuesto_detalle', pk=pres.idPresupuesto)


@login_required
def presupuesto_sena(request, pk):
    """Regla 3 y Regla 4: Registra la seña exacta del 50% y crea el pedido."""
    pres = get_object_or_404(Presupuesto, pk=pk)
    if pres.estadoPresupuesto != EstadoPresupuesto.APROBADO:
        messages.error(request, 'El presupuesto debe estar APROBADO para pagar la seña.')
        return redirect('core:presupuesto_detalle', pk=pres.idPresupuesto)

    if hasattr(pres, 'pedido') and pres.pedido:
        messages.info(request, 'Este presupuesto ya tiene un pedido asignado.')
        return redirect('core:pedidos')

    sena = pres.montoSena
    pago = Pago(
        presupuesto=pres,
        fechaPago=timezone.localdate(),
        montoPago=sena,
        medioPago=MedioPago.EFECTIVO,
        tipoPago=TipoPago.SENA,
        nroComprobante=f'SENA-{pres.idPresupuesto:05d}'
    )
    pago.procesarPago()

    # Creación automática de Pedido (Regla 4)
    pedido = Pedido.crearDesdePresupuesto(
        presupuesto=pres,
        responsable=request.user,
        fechaEntregaEstimada=timezone.localdate() + timedelta(days=15),
        fechaRecepcion=timezone.localdate()
    )
    messages.success(request, f'Seña de {sena} registrada y Pedido #{pedido.idPedido:04d} creado exitosamente.')
    return redirect('core:pedidos')


# ==============================================================================
# 5. PEDIDOS (Lista, estados, responsable y cambio de estado)
# ==============================================================================

@login_required
def pedidos(request):
    hoy = timezone.localdate()
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    # Regla 11: Filtrado de pedidos según rol del usuario responsable
    if hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser:
        qs = Pedido.objects.filter(responsable=request.user)
        filtro_usuario = request.user.username
        es_empleado = True
    else:
        qs = Pedido.objects.all()
        filtro_usuario = None
        es_empleado = False

    if estado:
        qs = qs.filter(estadoPedido=estado)
    if q:
        qs = qs.filter(
            Q(presupuesto__cliente__nombre__icontains=q) |
            Q(presupuesto__cliente__apellido__icontains=q) |
            Q(presupuesto__cliente__rucCliente__icontains=q) |
            Q(presupuesto__detalles__descripcionMueble__icontains=q)
        ).distinct()

    pedidos_lista = qs.select_related('presupuesto__cliente', 'responsable').prefetch_related('presupuesto__detalles').order_by('-idPedido')

    return render(request, 'core/pedidos.html', {
        'pedidos': pedidos_lista,
        'q': q,
        'estado_seleccionado': estado,
        'estados': EstadoPedido.choices,
        'filtro_usuario': filtro_usuario,
        'es_empleado': es_empleado,
        'hoy': hoy,
    })


@login_required
def pedido_actualizar_estado(request, pk):
    """Regla 8 y Regla 11: Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.
    El empleado solo puede actualizar pedidos asignados a él."""
    pedido = get_object_or_404(Pedido, pk=pk)
    if hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser:
        if pedido.responsable != request.user:
            messages.error(request, 'Acceso denegado: Solo puede actualizar pedidos asignados a usted (Regla 11).')
            return redirect('core:pedidos')

    if request.method == 'POST':
        form = CambiarEstadoPedidoForm(request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            try:
                pedido.actualizarEstado(nuevo_estado)
                messages.success(request, f'Pedido #{pedido.idPedido:04d} actualizado a «{pedido.get_estadoPedido_display()}».')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect('core:pedidos')


# ==============================================================================
# 6. INVENTARIO & MATERIALES (Stock actual y aviso de stock crítico)
# ==============================================================================

@login_required
def materiales(request):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    q = request.GET.get('q', '').strip()
    lista = Material.objects.filter(activo=True)
    if q:
        lista = lista.filter(Q(codigo__icontains=q) | Q(nombreMaterial__icontains=q))
    solo_bajo = request.GET.get('stock') == 'bajo'
    if solo_bajo:
        lista = lista.filter(stockActual__lte=F('stockMinimo'))

    return render(request, 'core/materiales.html', {
        'materiales': lista,
        'q': q,
        'solo_bajo': solo_bajo,
        'es_empleado': es_empleado,
    })


@login_required
def movimientos(request):
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    qs = MovimientoInventario.objects.select_related('material', 'pedido', 'compra').order_by('-fechaMovimiento', '-idMovimiento')
    if tipo:
        qs = qs.filter(tipoMovimiento=tipo)
    if q:
        qs = qs.filter(Q(material__nombreMaterial__icontains=q) | Q(motivoObservacion__icontains=q))

    return render(request, 'core/movimientos.html', {
        'movimientos': qs,
        'q': q,
        'tipo_seleccionado': tipo,
        'es_empleado': es_empleado,
    })


@login_required
def movimiento_crear(request):
    """Regla 6: El stock nunca puede quedar negativo.
    Sección 6: El empleado solo registra consumo/merma en taller."""
    es_empleado = hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, es_empleado=es_empleado)
        if form.is_valid():
            mov = form.save(commit=False)
            if es_empleado and mov.tipoMovimiento not in [TipoMovimiento.SALIDA_CONSUMO, TipoMovimiento.DESPERDICIO]:
                mov.tipoMovimiento = TipoMovimiento.SALIDA_CONSUMO
            mov.fechaMovimiento = timezone.localdate()
            try:
                mov.registrar()
                msg = (
                    f'Consumo de {mov.cantidadMovimiento} {mov.material.unidadMedida} registrado en {mov.material.nombreMaterial}.'
                    if es_empleado else
                    f'Movimiento de {mov.cantidadMovimiento} {mov.material.unidadMedida} registrado en {mov.material.nombreMaterial}.'
                )
                messages.success(request, msg)
                return redirect('core:movimientos')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = MovimientoInventarioForm(es_empleado=es_empleado)

    return render(request, 'core/movimiento_form.html', {'form': form, 'es_empleado': es_empleado})


# ==============================================================================
# 7. CAJA (Apertura, ingresos, egresos y cierre del día - Solo ADMIN)
# ==============================================================================

@requiere_permiso('gestionar_caja')
def caja(request):
    hoy = timezone.localdate()
    pagos_hoy = Pago.objects.filter(fechaPago=hoy).select_related('presupuesto__cliente')
    gastos_hoy = GastoOperativo.objects.filter(fechaGasto=hoy)
    pagos_prov_hoy = PagoProveedor.objects.filter(fechaPago=hoy).select_related('compra__proveedor')

    total_ingresos = sum((p.montoPago for p in pagos_hoy), Decimal('0.00'))
    total_egresos = sum((g.montoGasto for g in gastos_hoy), Decimal('0.00')) + sum((pp.montoPago for pp in pagos_prov_hoy), Decimal('0.00'))
    balance_neto = total_ingresos - total_egresos

    cierres_recientes = CierreCaja.objects.select_related('usuario').order_by('-fechaCierre')[:10]
    cierre_hoy = CierreCaja.objects.filter(fechaCierre=hoy).first()

    return render(request, 'core/caja.html', {
        'hoy': hoy,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance_neto': balance_neto,
        'pagos_hoy': pagos_hoy,
        'gastos_hoy': gastos_hoy,
        'pagos_prov_hoy': pagos_prov_hoy,
        'cierres': cierres_recientes,
        'cierre_hoy': cierre_hoy,
    })


@requiere_permiso('gestionar_caja')
def caja_cerrar(request):
    hoy = timezone.localdate()
    cierre, created = CierreCaja.objects.get_or_create(
        fechaCierre=hoy,
        defaults={'usuario': request.user}
    )
    if not created:
        cierre.usuario = request.user
        cierre.save()
    messages.success(request, f'Cierre de caja para {hoy.strftime("%d/%m/%Y")} registrado correctamente.')
    return redirect('core:caja')


@requiere_permiso('gestionar_caja')
def gasto_crear(request):
    """Regla 10: Compras de materiales no se registran como GastoOperativo."""
    if request.method == 'POST':
        form = GastoOperativoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.fechaGasto = timezone.localdate()
            gasto.save()
            messages.success(request, f'Gasto «{gasto.conceptoGasto}» registrado correctamente.')
            return redirect('core:caja')
    else:
        form = GastoOperativoForm()

    return render(request, 'core/gasto_form.html', {'form': form})


# ==============================================================================
# 8. COMPRAS Y PROVEEDORES (Solo ADMIN)
# ==============================================================================

@requiere_permiso('gestionar_compras')
def proveedores(request):
    q = request.GET.get('q', '').strip()
    qs = Proveedor.objects.prefetch_related('precios_materiales__material', 'compras__pagos')
    if q:
        qs = qs.filter(Q(razonSocial__icontains=q) | Q(rucProveedor__icontains=q) | Q(rubroMaterial__icontains=q))

    return render(request, 'core/proveedores.html', {
        'proveedores': qs.order_by('razonSocial'),
        'q': q,
    })


@requiere_permiso('gestionar_compras')
def compras(request):
    q = request.GET.get('q', '').strip()
    qs = Compra.objects.select_related('proveedor').prefetch_related('detalles__material', 'pagos').order_by('-fechaCompra', '-idCompra')
    if q:
        qs = qs.filter(Q(proveedor__razonSocial__icontains=q) | Q(proveedor__rucProveedor__icontains=q))

    return render(request, 'core/compras.html', {
        'compras': qs,
        'q': q,
    })


# ==============================================================================
# 9. AUDITORÍA (Regla 9 - Solo ADMIN)
# ==============================================================================

@requiere_permiso('respaldos_auditoria')
def auditoria(request):
    q = request.GET.get('q', '').strip()
    qs = RegistroCambio.objects.select_related('usuario').order_by('-fechaHora')[:100]
    if q:
        qs = qs.filter(Q(entidad__icontains=q) | Q(valorNuevo__icontains=q) | Q(valorAnterior__icontains=q))

    return render(request, 'core/auditoria.html', {
        'registros': qs,
        'q': q,
    })


# ==============================================================================
# 10. REPORTES Y EXPORTACIÓN A EXCEL Y PDF (Solo ADMIN)
# ==============================================================================

@requiere_permiso('reportes_economicos')
def reportes(request):
    return render(request, 'core/reportes.html')


@requiere_permiso('reportes_economicos')
def reporte_excel(request, tipo):
    """Exporta listados a CSV compatible con Excel con BOM UTF-8."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    writer = csv.writer(response, delimiter=';')

    if tipo == 'pedidos':
        response['Content-Disposition'] = 'attachment; filename="reporte_pedidos.csv"'
        writer.writerow(['ID Pedido', 'Cliente', 'Mueble', 'Responsable', 'Fecha Recepcion', 'Fecha Entrega Estimada', 'Estado', 'Total (Gs)', 'Saldo Pendiente (Gs)'])
        for p in Pedido.objects.select_related('presupuesto__cliente', 'responsable').all():
            writer.writerow([f"PED-{p.idPedido:04d}", p.presupuesto.cliente.obtenerNombreCompleto(), p.descripcion, p.responsable.username, p.fechaRecepcion, p.fechaEntregaEstimada, p.get_estadoPedido_display(), int(p.total), int(p.saldo)])

    elif tipo == 'presupuestos':
        response['Content-Disposition'] = 'attachment; filename="reporte_presupuestos.csv"'
        writer.writerow(['ID Presupuesto', 'Cliente', 'Fecha Emision', 'Modalidad Entrega', 'Mano de Obra (Gs)', 'Monto Total (Gs)', 'Seña 50% (Gs)', 'Saldo Pendiente (Gs)', 'Estado'])
        for pres in Presupuesto.objects.select_related('cliente', 'entrega').all():
            modalidad = pres.entrega.get_modalidadEntrega_display() if hasattr(pres, 'entrega') else 'No especificada'
            writer.writerow([f"#{pres.idPresupuesto:05d}", pres.cliente.obtenerNombreCompleto(), pres.fechaEmision, modalidad, int(pres.costoManoObra), int(pres.montoTotal), int(pres.montoSena), int(pres.saldoPendiente), pres.get_estadoPresupuesto_display()])

    elif tipo == 'inventario':
        response['Content-Disposition'] = 'attachment; filename="reporte_inventario.csv"'
        writer.writerow(['Codigo', 'Material', 'Categoria', 'Unidad', 'Costo Unitario (Gs)', 'Stock Actual', 'Stock Minimo', 'Estado Stock', 'Valorizacion (Gs)'])
        for m in Material.objects.filter(activo=True):
            estado_stk = 'CRITICO' if m.esStockCritico() else 'Normal'
            writer.writerow([m.codigo, m.nombreMaterial, m.categoria, m.unidadMedida, int(m.precioCosto), m.stockActual, m.stockMinimo, estado_stk, int(m.valor_stock)])

    elif tipo == 'caja':
        response['Content-Disposition'] = 'attachment; filename="reporte_cierre_caja.csv"'
        writer.writerow(['Fecha Cierre', 'Responsable', 'Total Ingresos (Gs)', 'Total Egresos (Gs)', 'Balance Neto (Gs)'])
        for c in CierreCaja.objects.select_related('usuario').all():
            writer.writerow([c.fechaCierre, c.usuario.username, int(c.totalIngresos), int(c.totalEgresos), int(c.balanceNeto)])

    elif tipo == 'clientes':
        response['Content-Disposition'] = 'attachment; filename="reporte_clientes.csv"'
        writer.writerow(['Nombre Completo', 'RUC', 'CI', 'Telefono', 'Direccion', 'Fecha Registro', 'Cant. Presupuestos', 'Cant. Pedidos'])
        for cli in Cliente.objects.all():
            writer.writerow([cli.obtenerNombreCompleto(), cli.rucCliente, cli.ci, cli.telefono, cli.direccion, cli.fechaRegistro, len(cli.consultarPresupuestos()), len(cli.consultarHistorialPedidos())])

    else:
        raise Http404('Reporte inexistente')

    return response


@requiere_permiso('reportes_economicos')
def reporte_imprimir(request, tipo):
    hoy = timezone.now()
    titulos = {
        'pedidos': 'Reporte de Pedidos de Taller',
        'presupuestos': 'Reporte de Presupuestos Emitidos',
        'inventario': 'Reporte de Inventario y Stock de Materiales',
        'caja': 'Reporte Financiero y Cierres de Caja',
        'clientes': 'Reporte de Clientes Registrados',
    }
    if tipo not in titulos:
        raise Http404('Reporte inexistente')

    if tipo == 'pedidos':
        datos = Pedido.objects.select_related('presupuesto__cliente', 'responsable').all().order_by('-idPedido')
    elif tipo == 'presupuestos':
        datos = Presupuesto.objects.select_related('cliente', 'entrega').all().order_by('-idPresupuesto')
    elif tipo == 'inventario':
        datos = Material.objects.filter(activo=True).order_by('nombreMaterial')
    elif tipo == 'caja':
        datos = CierreCaja.objects.select_related('usuario').all().order_by('-fechaCierre')
    elif tipo == 'clientes':
        datos = Cliente.objects.all().order_by('apellido', 'nombre')

    return render(request, 'core/reporte_imprimir.html', {
        'tipo': tipo,
        'titulo_reporte': titulos[tipo],
        'datos': datos,
        'hoy': hoy,
    })


@login_required
def modulo(request, slug):
    seccion, titulo = titulo_por_slug(slug)
    if titulo is None:
        raise Http404('Módulo inexistente')
    return render(request, 'core/en_construccion.html', {'seccion': seccion, 'titulo': titulo})
