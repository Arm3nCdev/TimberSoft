from django import forms
from .models import Cliente, DetallePresupuesto


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'


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