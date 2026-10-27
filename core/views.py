from datetime import timedelta

from django.db.models import F, Q, Sum
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from .menu import titulo_por_slug
from .models import Material, OrdenTrabajo


def dashboard(request):
    hoy = timezone.localdate()
    Estado = OrdenTrabajo.Estado
    abiertos = OrdenTrabajo.objects.exclude(estado=Estado.ENTREGADO)
    stock_bajo = Material.objects.filter(activo=True, stock__lte=F('stock_minimo'))

    contexto = {
        'en_produccion': abiertos.filter(estado=Estado.PRODUCCION).count(),
        'presupuestos': abiertos.filter(estado=Estado.PRESUPUESTO).count(),
        'entregas_semana': abiertos.filter(fecha_entrega__range=(hoy, hoy + timedelta(days=7))).count(),
        'atrasados': abiertos.filter(fecha_entrega__lt=hoy).count(),
        'saldo_cobrar': abiertos.exclude(estado=Estado.PRESUPUESTO)
                                .aggregate(t=Sum(F('total') - F('sena')))['t'] or 0,
        'proximas_entregas': abiertos.exclude(estado=Estado.PRESUPUESTO)
                                     .select_related('cliente').order_by('fecha_entrega')[:6],
        'stock_bajo': stock_bajo.select_related('categoria')[:6],
        'cantidad_stock_bajo': stock_bajo.count(),
        'hoy': hoy,
    }
    return render(request, 'core/dashboard.html', contexto)


def materiales(request):
    q = request.GET.get('q', '').strip()
    lista = Material.objects.filter(activo=True).select_related('categoria')
    if q:
        lista = lista.filter(Q(codigo__icontains=q) | Q(descripcion__icontains=q))
    solo_bajo = request.GET.get('stock') == 'bajo'
    if solo_bajo:
        lista = lista.filter(stock__lte=F('stock_minimo'))
    return render(request, 'core/materiales.html', {'materiales': lista, 'q': q, 'solo_bajo': solo_bajo})


def modulo(request, slug):
    seccion, titulo = titulo_por_slug(slug)
    if titulo is None:
        raise Http404('Módulo inexistente')
    return render(request, 'core/en_construccion.html', {'seccion': seccion, 'titulo': titulo})
