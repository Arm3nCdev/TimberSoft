from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Cliente,
    Presupuesto,
    DetallePresupuesto,
    Entrega,
    ModalidadEntrega,
    Material,
    MaterialRequerido,
    MovimientoInventario,
    TipoMovimiento,
    GastoOperativo,
    EstadoPedido,
)


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'ci', 'rucCliente', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Pérez'}),
            'ci': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. 3456789'}),
            'rucCliente': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. 3456789-1'}),
            'telefono': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. 0981 123456'}),
            'direccion': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Asunción, Calle Palma'}),
        }


class PresupuestoCabeceraForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['cliente', 'fechaEmision', 'costoManoObra']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'campo-input'}),
            'fechaEmision': forms.DateInput(attrs={'class': 'campo-input', 'type': 'date'}),
            'costoManoObra': forms.NumberInput(attrs={'class': 'campo-input', 'step': '1000', 'placeholder': '0'}),
        }


class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['modalidadEntrega', 'direccionEntrega', 'costoFlete', 'observaciones']
        widgets = {
            'modalidadEntrega': forms.Select(attrs={'class': 'campo-input'}),
            'direccionEntrega': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Dirección para entrega a domicilio'}),
            'costoFlete': forms.NumberInput(attrs={'class': 'campo-input', 'step': '1000', 'placeholder': '0'}),
            'observaciones': forms.Textarea(attrs={'class': 'campo-input', 'rows': 2, 'placeholder': 'Indicaciones de entrega'}),
        }


class DetallePresupuestoForm(forms.ModelForm):
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True),
        required=False,
        empty_label='(Opcional) Material principal',
        widget=forms.Select(attrs={'class': 'campo-input'})
    )
    cantidad_material = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'campo-input', 'step': '0.1', 'placeholder': 'Cant. mat.'})
    )

    class Meta:
        model = DetallePresupuesto
        fields = ['descripcionMueble', 'largo', 'ancho', 'alto', 'colorTerminacion', 'cantidad', 'margen']
        widgets = {
            'descripcionMueble': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Mesa de comedor 8 sillas'}),
            'largo': forms.NumberInput(attrs={'class': 'campo-input', 'step': '0.01', 'placeholder': 'Largo (m)'}),
            'ancho': forms.NumberInput(attrs={'class': 'campo-input', 'step': '0.01', 'placeholder': 'Ancho (m)'}),
            'alto': forms.NumberInput(attrs={'class': 'campo-input', 'step': '0.01', 'placeholder': 'Alto (m)'}),
            'colorTerminacion': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Lapacho lustrado'}),
            'cantidad': forms.NumberInput(attrs={'class': 'campo-input', 'min': '1'}),
            'margen': forms.NumberInput(attrs={'class': 'campo-input', 'step': '1000', 'placeholder': 'Margen ₲'}),
        }


class MovimientoInventarioForm(forms.ModelForm):
    def __init__(self, *args, es_empleado=False, **kwargs):
        super().__init__(*args, **kwargs)
        if es_empleado:
            self.fields['tipoMovimiento'].choices = [
                (TipoMovimiento.SALIDA_CONSUMO, 'Salida por consumo en taller'),
                (TipoMovimiento.DESPERDICIO, 'Desperdicio o merma de trabajo'),
            ]
            self.fields['tipoMovimiento'].initial = TipoMovimiento.SALIDA_CONSUMO
            self.fields['motivoObservacion'].widget.attrs['placeholder'] = 'Indique mueble, pedido o motivo del consumo'

    class Meta:
        model = MovimientoInventario
        fields = ['material', 'tipoMovimiento', 'cantidadMovimiento', 'motivoObservacion']
        widgets = {
            'material': forms.Select(attrs={'class': 'campo-input'}),
            'tipoMovimiento': forms.Select(attrs={'class': 'campo-input'}),
            'cantidadMovimiento': forms.NumberInput(attrs={'class': 'campo-input', 'step': '0.01', 'min': '0.01'}),
            'motivoObservacion': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Motivo o detalle del ajuste'}),
        }


class GastoOperativoForm(forms.ModelForm):
    class Meta:
        model = GastoOperativo
        fields = ['conceptoGasto', 'montoGasto', 'comprobanteRef']
        widgets = {
            'conceptoGasto': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. Electricidad ANDE taller'}),
            'montoGasto': forms.NumberInput(attrs={'class': 'campo-input', 'step': '1000', 'placeholder': '0'}),
            'comprobanteRef': forms.TextInput(attrs={'class': 'campo-input', 'placeholder': 'Ej. FAC-001-002-12345'}),
        }


class CambiarEstadoPedidoForm(forms.Form):
    nuevo_estado = forms.ChoiceField(
        choices=EstadoPedido.choices,
        widget=forms.Select(attrs={'class': 'campo-input'})
    )


class ImagenMuebleForm(forms.ModelForm):
    class Meta:
        model = DetallePresupuesto
        fields = ['imagen']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagen'].required = True
        self.fields['imagen'].help_text = 'Seleccioná una imagen de hasta 5 MB.'
        self.fields['imagen'].widget.attrs.update({
            'accept': 'image/*',
            'class': 'input-imagen-mueble',
        })
