from django.db import models


class TipoIVA(models.IntegerChoices):
    """Tasas de IVA vigentes en Paraguay (Ley 6380/2019)."""
    EXENTA = 0, 'Exenta'
    IVA_5 = 5, 'IVA 5%'
    IVA_10 = 10, 'IVA 10%'


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría'

    def __str__(self):
        return self.nombre


class Material(models.Model):
    """Maderas, tableros, herrajes e insumos del taller."""
    UNIDADES = [
        ('PT', 'Pie tablar'),
        ('PL', 'Placa'),
        ('UN', 'Unidad'),
        ('MT', 'Metro'),
        ('LT', 'Litro'),
        ('KG', 'Kilogramo'),
        ('CJ', 'Caja'),
    ]

    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='materiales')
    unidad = models.CharField(max_length=2, choices=UNIDADES, default='UN')
    # Montos en guaraníes: el ₲ no usa decimales, por eso enteros.
    precio_costo = models.PositiveBigIntegerField(help_text='Costo por unidad, IVA incluido')
    iva = models.PositiveSmallIntegerField(choices=TipoIVA.choices, default=TipoIVA.IVA_10)
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['descripcion']
        verbose_name_plural = 'materiales'

    def __str__(self):
        return f'{self.codigo} - {self.descripcion}'

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    @property
    def valor_stock(self):
        return round(self.stock * self.precio_costo)


class Cliente(models.Model):
    razon_social = models.CharField(max_length=150)
    ruc = models.CharField('RUC / CI', max_length=20, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ['razon_social']

    def __str__(self):
        return f'{self.razon_social} ({self.ruc})'


class OrdenTrabajo(models.Model):
    """Un trabajo a pedido: mueble, abertura, etc. Nace como presupuesto."""

    class Estado(models.TextChoices):
        PRESUPUESTO = 'PRESUPUESTO', 'Presupuesto'
        PRODUCCION = 'PRODUCCION', 'En producción'
        TERMINADO = 'TERMINADO', 'Terminado'
        ENTREGADO = 'ENTREGADO', 'Entregado'

    numero = models.PositiveIntegerField(unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='trabajos')
    descripcion = models.CharField(max_length=200)
    madera = models.CharField(max_length=60, blank=True, help_text='Ej.: lapacho, cedro, MDF melamina')
    estado = models.CharField(max_length=11, choices=Estado.choices, default=Estado.PRESUPUESTO)
    fecha_pedido = models.DateField()
    fecha_entrega = models.DateField(null=True, blank=True)
    total = models.PositiveBigIntegerField(help_text='Precio acordado, IVA incluido')
    sena = models.PositiveBigIntegerField('seña', default=0)

    class Meta:
        ordering = ['-numero']
        verbose_name = 'orden de trabajo'
        verbose_name_plural = 'órdenes de trabajo'

    def __str__(self):
        return f'OT {self.numero:05d} - {self.descripcion}'

    @property
    def saldo(self):
        return self.total - self.sena
