from datetime import timedelta

from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST

import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from .menu import titulo_por_slug
from .forms import ClienteForm, ImagenMuebleForm
from .models import (
    Material,
    Pedido,
    Presupuesto,
    Cliente,
    Proveedor,
    Compra,
    MovimientoInventario,
    GastoOperativo,
    PagoProveedor,
    Pago,
    CierreCaja,
    RegistroCambio,
    EstadoPedido,
    EstadoPresupuesto,
    RolEnum,
    DetallePresupuesto,
    MaterialRequerido,
    Entrega,
    ModalidadEntrega,
    AccionAuditoria,
)


def dashboard(request):
    hoy = timezone.localdate()

    # Regla 11: Cada Pedido tiene un Usuario responsable. El EMPLEADO solo ve y actualiza
    # los pedidos que tiene asignados; el ADMIN ve todos.
    if request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser:
        pedidos_base = Pedido.objects.filter(responsable=request.user)
        es_empleado = True
    else:
        pedidos_base = Pedido.objects.all()
        es_empleado = False

    abiertos = pedidos_base.exclude(estadoPedido=EstadoPedido.ENTREGADO)
    stock_bajo = Material.objects.filter(activo=True, stockActual__lte=F('stockMinimo'))
    saldo_total = sum((p.saldo for p in abiertos), Decimal('0.00'))

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


def pedidos(request):
    hoy = timezone.localdate()
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    # Regla 11: Filtrado de pedidos según rol del usuario responsable
    if request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol == RolEnum.EMPLEADO and not request.user.is_superuser:
        qs = Pedido.objects.filter(responsable=request.user)
        filtro_usuario = request.user.username
    else:
        qs = Pedido.objects.all()
        filtro_usuario = None

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
        'hoy': hoy,
    })


def nuevo_presupuesto(request):
    clientes = Cliente.objects.all().order_by('apellido', 'nombre')
    materiales = Material.objects.filter(activo=True).order_by('nombreMaterial')

    contexto = {
        'clientes': clientes,
        'materiales': materiales,
        'modalidades': ModalidadEntrega.choices,
    }

    if request.method == 'POST':
        try:
            cliente = Cliente.objects.get(pk=request.POST.get('cliente'))

            modalidad = request.POST.get('modalidadEntrega')
            modalidades_validas = [opcion[0] for opcion in ModalidadEntrega.choices]

            if modalidad not in modalidades_validas:
                raise ValueError('Seleccioná una modalidad de entrega válida.')

            def obtener_decimal(nombre, predeterminado='0'):
                valor = request.POST.get(nombre, predeterminado)
                numero = Decimal(valor or predeterminado)

                if numero < 0:
                    raise ValueError('Los importes y cantidades no pueden ser negativos.')

                return numero

            costo_mano_obra = obtener_decimal('costoManoObra')
            costo_flete = obtener_decimal('costoFlete')

            direccion = request.POST.get('direccionEntrega', '').strip()

            if modalidad == ModalidadEntrega.DOMICILIO and not direccion:
                raise ValueError('Ingresá la dirección de entrega.')

            if modalidad != ModalidadEntrega.DOMICILIO:
                costo_flete = Decimal('0')
                direccion = ''

            indices_muebles = sorted({
                int(coincidencia.group(1))
                for clave in request.POST.keys()
                if (coincidencia := re.match(
                    r'^muebles\[(\d+)\]\[descripcion\]$', clave
                ))
            })

            if not indices_muebles:
                raise ValueError('Agregá al menos un mueble al presupuesto.')

            with transaction.atomic():

                presupuesto = Presupuesto.objects.create(
                    cliente=cliente,
                    costoManoObra=costo_mano_obra,
                    estadoPresupuesto=EstadoPresupuesto.PENDIENTE,
                )

                for indice in indices_muebles:
                    descripcion = request.POST.get(
                        f'muebles[{indice}][descripcion]', ''
                    ).strip()

                    if not descripcion:
                        raise ValueError('Todos los muebles deben tener una descripción.')

                    cantidad = int(
                        request.POST.get(f'muebles[{indice}][cantidad]', '1')
                    )

                    if cantidad < 1:
                        raise ValueError('La cantidad de muebles debe ser al menos 1.')

                    detalle = DetallePresupuesto.objects.create(
                        presupuesto=presupuesto,
                        descripcionMueble=descripcion,
                        largo=obtener_decimal(f'muebles[{indice}][largo]'),
                        ancho=obtener_decimal(f'muebles[{indice}][ancho]'),
                        alto=obtener_decimal(f'muebles[{indice}][alto]'),
                        detalleMedidas=request.POST.get(
                            f'muebles[{indice}][detalleMedidas]', ''
                        ).strip(),
                        colorTerminacion=request.POST.get(
                            f'muebles[{indice}][color]', ''
                        ).strip(),
                        cantidad=cantidad,
                        margen=obtener_decimal(
                            f'muebles[{indice}][margen]'
                        ),
                    )

                    patron_material = re.compile(
                        rf'^muebles\[{indice}\]\[materiales\]\[(\d+)\]\[material\]$'
                    )

                    indices_materiales = sorted({
                        int(coincidencia.group(1))
                        for clave in request.POST.keys()
                        if (coincidencia := patron_material.match(clave))
                    })

                    materiales_agregados = 0

                    for indice_material in indices_materiales:
                        prefijo = (
                            f'muebles[{indice}]'
                            f'[materiales][{indice_material}]'
                        )

                        material_id = request.POST.get(
                            f'{prefijo}[material]'
                        )

                        if not material_id:
                            continue

                        material = Material.objects.get(
                            pk=material_id,
                            activo=True
                        )

                        cantidad_material = obtener_decimal(
                            f'{prefijo}[cantidad]'
                        )

                        if cantidad_material <= 0:
                            raise ValueError(
                                'La cantidad de cada material debe ser mayor que cero.'
                            )

                        MaterialRequerido.objects.create(
                            detallePresupuesto=detalle,
                            material=material,
                            cantidadRequerida=cantidad_material,
                        )

                        materiales_agregados += 1

                    if materiales_agregados == 0:
                        raise ValueError(
                            f'El mueble "{descripcion}" debe tener al menos un material.'
                        )

                Entrega.objects.create(
                    presupuesto=presupuesto,
                    modalidadEntrega=modalidad,
                    direccionEntrega=direccion,
                    costoFlete=costo_flete,
                )

                RegistroCambio.objects.create(
                    usuario=request.user if request.user.is_authenticated else None,
                    entidad='Presupuesto',
                    idEntidad=presupuesto.pk,
                    accion=AccionAuditoria.CREAR,
                    valorNuevo=(
                        f'Presupuesto creado para {cliente}. '
                        f'Estado: Pendiente. '
                        f'Total: {presupuesto.montoTotal}'
                    ),
                )

            return redirect('core:presupuestos')

        except Cliente.DoesNotExist:
            contexto['error'] = 'El cliente seleccionado no existe.'
        except Material.DoesNotExist:
            contexto['error'] = 'Uno de los materiales seleccionados no existe o está inactivo.'
        except (ValueError, InvalidOperation, TypeError):
            contexto['error'] = (
                'Verificá los datos ingresados. Revisá cantidades, medidas e importes.'
            )

    return render(request, 'core/nuevo_presupuesto.html', contexto)


def presupuestos(request):
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
    })


@require_POST
def subir_imagen_mueble(request, detalle_id):
    detalle = get_object_or_404(DetallePresupuesto, pk=detalle_id)
    form = ImagenMuebleForm(request.POST, request.FILES, instance=detalle)

    if form.is_valid():
        form.save()
        messages.success(request, 'La imagen del mueble se cargó correctamente.')
    else:
        errores = ' '.join(form.errors.get('imagen', ['Verificá el archivo seleccionado.']))
        messages.error(request, f'No se pudo cargar la imagen. {errores}')

    return redirect('core:presupuestos')


def materiales(request):
    q = request.GET.get('q', '').strip()
    lista = Material.objects.filter(activo=True)
    if q:
        lista = lista.filter(Q(codigo__icontains=q) | Q(nombreMaterial__icontains=q))
    solo_bajo = request.GET.get('stock') == 'bajo'
    if solo_bajo:
        lista = lista.filter(stockActual__lte=F('stockMinimo'))
    return render(request, 'core/materiales.html', {'materiales': lista, 'q': q, 'solo_bajo': solo_bajo})


def movimientos(request):
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
    })


def proveedores(request):
    q = request.GET.get('q', '').strip()
    qs = Proveedor.objects.prefetch_related('precios_materiales__material', 'compras__pagos')
    if q:
        qs = qs.filter(Q(razonSocial__icontains=q) | Q(rucProveedor__icontains=q) | Q(rubroMaterial__icontains=q))

    return render(request, 'core/proveedores.html', {
        'proveedores': qs.order_by('razonSocial'),
        'q': q,
    })


def compras(request):
    q = request.GET.get('q', '').strip()
    qs = Compra.objects.select_related('proveedor').prefetch_related('detalles__material', 'pagos').order_by('-fechaCompra', '-idCompra')
    if q:
        qs = qs.filter(Q(proveedor__razonSocial__icontains=q) | Q(proveedor__rucProveedor__icontains=q))

    return render(request, 'core/compras.html', {
        'compras': qs,
        'q': q,
    })


def clientes(request):
    q = request.GET.get('q', '').strip()
    qs = Cliente.objects.prefetch_related('presupuestos__pedido').order_by('apellido', 'nombre')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(rucCliente__icontains=q) | Q(ci__icontains=q))

    return render(request, 'core/clientes.html', {
        'clientes': qs,
        'q': q,
    })


def cliente_nuevo(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:clientes')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form})

def caja(request):
    hoy = timezone.localdate()
    # Regla 10: Se suman ingresos por pagos de clientes; egresos por gastos operativos y pagos a proveedores
    pagos_hoy = Pago.objects.filter(fechaPago=hoy).select_related('presupuesto__cliente')
    gastos_hoy = GastoOperativo.objects.filter(fechaGasto=hoy)
    pagos_prov_hoy = PagoProveedor.objects.filter(fechaPago=hoy).select_related('compra__proveedor')

    total_ingresos = sum((p.montoPago for p in pagos_hoy), Decimal('0.00'))
    total_egresos = sum((g.montoGasto for g in gastos_hoy), Decimal('0.00')) + sum((pp.montoPago for pp in pagos_prov_hoy), Decimal('0.00'))
    balance_neto = total_ingresos - total_egresos

    cierres_recientes = CierreCaja.objects.select_related('usuario').order_by('-fechaCierre')[:10]

    return render(request, 'core/caja.html', {
        'hoy': hoy,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance_neto': balance_neto,
        'pagos_hoy': pagos_hoy,
        'gastos_hoy': gastos_hoy,
        'pagos_prov_hoy': pagos_prov_hoy,
        'cierres': cierres_recientes,
    })


def auditoria(request):
    q = request.GET.get('q', '').strip()
    # Regla 9: Visualización de las acciones críticas registradas automáticamente
    qs = RegistroCambio.objects.select_related('usuario').order_by('-fechaHora')[:100]
    if q:
        qs = qs.filter(Q(entidad__icontains=q) | Q(valorNuevo__icontains=q) | Q(valorAnterior__icontains=q))

    return render(request, 'core/auditoria.html', {
        'registros': qs,
        'q': q,
    })


def modulo(request, slug):
    seccion, titulo = titulo_por_slug(slug)
    if titulo is None:
        raise Http404('Módulo inexistente')
    return render(request, 'core/en_construccion.html', {'seccion': seccion, 'titulo': titulo})
