from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver


# ==============================================================================
# 2. ENUMERACIONES
# ==============================================================================

class RolEnum(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    EMPLEADO = 'EMPLEADO', 'Empleado'


class EstadoPresupuesto(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADO = 'APROBADO', 'Aprobado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class EstadoPedido(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    EN_PROCESO = 'EN_PROCESO', 'En proceso'
    TERMINADO = 'TERMINADO', 'Terminado'
    ENTREGADO = 'ENTREGADO', 'Entregado'


class ModalidadEntrega(models.TextChoices):
    RETIRO_TALLER = 'RETIRO_TALLER', 'Retiro en taller'
    DOMICILIO = 'DOMICILIO', 'Entrega a domicilio'


class TipoPago(models.TextChoices):
    SENA = 'SENA', 'Seña'
    PARCIAL = 'PARCIAL', 'Pago parcial'
    SALDO = 'SALDO', 'Saldo'


class MedioPago(models.TextChoices):
    EFECTIVO = 'EFECTIVO', 'Efectivo'
    TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'


class TipoMovimiento(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    SALIDA_CONSUMO = 'SALIDA_CONSUMO', 'Salida por consumo'
    DESPERDICIO = 'DESPERDICIO', 'Desperdicio'


class UnidadMedida(models.TextChoices):
    UNIDAD = 'UNIDAD', 'Unidad'
    METRO = 'METRO', 'Metro'
    M2 = 'M2', 'Metro cuadrado (m²)'
    LITRO = 'LITRO', 'Litro'
    KG = 'KG', 'Kilogramo'


class AccionAuditoria(models.TextChoices):
    CREAR = 'CREAR', 'Crear'
    MODIFICAR = 'MODIFICAR', 'Modificar'
    ELIMINAR = 'ELIMINAR', 'Eliminar'

class estadoFactura(models.TextChoices):
    EMITIDA='Emitida','Emitida'
    ANULADA='Anulada','Anulada'

class Timbrado(models.Model):
    idTmbrado=models.AutoField(primary_key=True)
    numeroTimbrado = models.CharField('Número de timbrado', max_length=20, unique=True)
    establecimiento = models.CharField('Establecimiento', max_length=3, default='001')
    puntoExpedicion = models.CharField('Punto de expedición', max_length=3, default='001')
    numeroDesde = models.PositiveIntegerField('Numeración desde')
    numeroHasta = models.PositiveIntegerField('Numeración hasta')
    ultimoNumeroEmitido = models.PositiveIntegerField('Último número emitido', default=0)
    fechaInicioVigencia = models.DateField('Inicio de vigencia')
    fechaFinVigencia = models.DateField('Fin de vigencia')
    activo = models.BooleanField('Activo', default=True)

class Meta:
    verbose_name='Timbrado'
    verbose_name_plural='Timbrados'

def __str__(self):
    return f"Timbrado {self.numeroTimbrado} ({self.establecimiento}-{self.puntoExpedicion})"

def estadoVigente(self, fecha=None):
    fecha=fecha or timezone.localdate()
    return (
        self.activo
        and self.fechaInicioVigencia <= fecha <= self.fechaFinVigencia
        and self.ultimoNumeroEmitido < self.numeroHasta
    )
    def obtenerSiguienteNumero(self):
        if not self.estaVigente():
            raise ValidationError("El timbrado no está vigente o agotó su rango autorizado.")
        siguiente = max(self.ultimoNumeroEmitido + 1, self.numeroDesde)
        if siguiente > self.numeroHasta:
            raise ValidationError("Se alcanzó el límite máximo de numeración del timbrado.")
        return f"{self.establecimiento}-{self.puntoExpedicion}-{siguiente:07d}", siguiente


class Factura(models.Model):
    idFactura = models.AutoField(primary_key=True)
    pedido = models.OneToOneField('Pedido', on_delete=models.PROTECT, related_name='factura')
    timbrado = models.ForeignKey(Timbrado, on_delete=models.PROTECT, related_name='facturas')
    numeroFactura = models.CharField('Número de factura', max_length=20, unique=True)
    fechaEmision = models.DateField('Fecha de emisión', default=timezone.localdate)
    porcentajeIva = models.DecimalField('Tasa IVA (%)', max_digits=5, decimal_places=2, default=Decimal('10.00'))
    montoGravado = models.DecimalField('Gravada', max_digits=14, decimal_places=2, default=Decimal('0.00'))
    montoIva = models.DecimalField('Liquidación IVA', max_digits=14, decimal_places=2, default=Decimal('0.00'))
    montoTotal = models.DecimalField('Total factura', max_digits=14, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField('Estado', max_length=15, choices=estadoFactura.choices, default=estadoFactura.EMITIDA)

    class Meta:
        verbose_name = 'factura'
        verbose_name_plural = 'facturas'
        ordering = ['-idFactura']

    def __str__(self):
        return f"Factura {self.numeroFactura} (Timbrado {self.timbrado.numeroTimbrado})"

    @classmethod
    def emitirDesdePedido(cls, pedido, timbrado, porcentaje_iva=Decimal('10.00'), iva_incluido=True):
        if hasattr(pedido, 'factura'):
            raise ValidationError("Este pedido ya tiene una factura emitida.")
        if not timbrado.estaVigente():
            raise ValidationError("El timbrado seleccionado no está vigente o no tiene numeración disponible.")

        total = pedido.total
        tasa = Decimal(str(porcentaje_iva))

        # Si el precio ya incluye IVA (ej. 10% -> divisor 1.10)
        if iva_incluido:
            divisor = Decimal('1.00') + (tasa / Decimal('100.00'))
            gravada = (total / divisor).quantize(Decimal('0.01'))
            iva = (total - gravada).quantize(Decimal('0.01'))
            total_final = total
        else:
            gravada = total.quantize(Decimal('0.01'))
            iva = (gravada * (tasa / Decimal('100.00'))).quantize(Decimal('0.01'))
            total_final = gravada + iva

        numero_formateado, correlativo = timbrado.obtenerSiguienteNumero()
        timbrado.ultimoNumeroEmitido = correlativo
        timbrado.save(update_fields=['ultimoNumeroEmitido'])

        return cls.objects.create(
            pedido=pedido,
            timbrado=timbrado,
            numeroFactura=numero_formateado,
            porcentajeIva=tasa,
            montoGravado=gravada,
            montoIva=iva,
            montoTotal=total_final,
        )
# Matriz de permisos según sección 6 del documento
PERMISOS_POR_ROL = {
    RolEnum.ADMIN: [
        'gestionar_clientes',
        'gestionar_presupuestos',
        'aprobar_presupuesto',
        'gestionar_pedidos',
        'gestionar_inventario',
        'gestionar_compras',
        'gestionar_caja',
        'reportes_economicos',
        'gestionar_usuarios',
        'respaldos_auditoria',
    ],
    RolEnum.EMPLEADO: [
        'gestionar_clientes',
        'gestionar_presupuestos',
        'aprobar_presupuesto',
        'gestionar_pedidos',  # Solo los asignados
        'gestionar_inventario',
    ],
}


# ==============================================================================
# 3. CLASES Y RELACIONES
# ==============================================================================

class Persona(models.Model):
    """Clase base de personas. Modela la abstracción general de la cual
    heredan Cliente y Usuario compartiendo idPersona."""
    idPersona = models.AutoField(primary_key=True)
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    direccion = models.CharField('Dirección', max_length=200, blank=True)
    ci = models.CharField('Cédula de Identidad', max_length=20, unique=True)

    class Meta:
        verbose_name = 'persona'
        verbose_name_plural = 'personas'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return self.obtenerNombreCompleto()

    def obtenerNombreCompleto(self):
        return f"{self.nombre} {self.apellido}".strip()

    def actualizarDatosContacto(self, telefono=None, direccion=None):
        cambios = []
        if telefono is not None:
            self.telefono = telefono
            cambios.append('telefono')
        if direccion is not None:
            self.direccion = direccion
            cambios.append('direccion')
        if cambios:
            self.save(update_fields=cambios)


class Cliente(Persona):
    """Cliente del taller. Hereda idPersona de Persona."""
    rucCliente = models.CharField('RUC / CI del Cliente', max_length=20, unique=True)
    fechaRegistro = models.DateField('Fecha de registro', default=timezone.localdate)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.obtenerNombreCompleto()} (RUC: {self.rucCliente})"

    @property
    def razon_social(self):
        return self.obtenerNombreCompleto()

    @property
    def ruc(self):
        return self.rucCliente

    def consultarHistorialPedidos(self):
        return list(Pedido.objects.filter(presupuesto__cliente=self).select_related('presupuesto'))

    def consultarPresupuestos(self):
        return list(self.presupuestos.all())


class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        extra_fields.setdefault('rol', RolEnum.EMPLEADO)
        extra_fields.setdefault('activo', True)
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('rol', RolEnum.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('activo', True)
        extra_fields.setdefault('nombre', 'Administrador')
        extra_fields.setdefault('apellido', 'Sistema')
        extra_fields.setdefault('ci', f"ADMIN-{username}")
        return self.create_user(username, password, **extra_fields)


class Usuario(Persona, AbstractBaseUser, PermissionsMixin):
    """Usuario del sistema. Hereda idPersona de Persona."""
    username = models.CharField('Usuario', max_length=50, unique=True)
    rol = models.CharField('Rol', max_length=20, choices=RolEnum.choices, default=RolEnum.EMPLEADO)
    activo = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Es personal administrativo', default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='grupos',
        blank=True,
        related_name='usuario_set',
        related_query_name='usuario',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='permisos de usuario',
        blank=True,
        related_name='usuario_set',
        related_query_name='usuario',
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, val):
        self.activo = bool(val)

    @property
    def passwordHash(self):
        return self.password

    def iniciarSesion(self, username, password):
        from django.contrib.auth import authenticate
        return authenticate(username=username, password=password) is not None

    def cerrarSesion(self):
        pass

    def validarPermiso(self, permiso):
        if self.is_superuser or self.rol == RolEnum.ADMIN:
            return True
        return permiso in PERMISOS_POR_ROL.get(self.rol, [])

    def obtenerPermisos(self):
        if self.is_superuser or self.rol == RolEnum.ADMIN:
            return PERMISOS_POR_ROL.get(RolEnum.ADMIN, [])
        return PERMISOS_POR_ROL.get(self.rol, [])

    def obtenerPedidosAsignados(self):
        return list(self.pedidos_asignados.all())


class Proveedor(models.Model):
    idProveedor = models.AutoField(primary_key=True)
    rucProveedor = models.CharField('RUC del proveedor', max_length=20, unique=True)
    razonSocial = models.CharField('Razón social', max_length=150)
    rubroMaterial = models.CharField('Rubro de material', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    direccion = models.CharField('Dirección', max_length=200, blank=True)

    class Meta:
        verbose_name = 'proveedor'
        verbose_name_plural = 'proveedores'
        ordering = ['razonSocial']

    def __str__(self):
        return f"{self.razonSocial} ({self.rucProveedor})"

    def obtenerCatalogoMateriales(self):
        return list(self.precios_materiales.filter(vigente=True).select_related('material'))

    def obtenerDeudaPendiente(self):
        return sum((c.saldoPendiente for c in self.compras.all()), Decimal('0.00'))


class Material(models.Model):
    idMaterial = models.AutoField(primary_key=True)
    codigo = models.CharField('Código', max_length=30, unique=True)
    nombreMaterial = models.CharField('Nombre del material', max_length=200)
    unidadMedida = models.CharField('Unidad de medida', max_length=10, choices=UnidadMedida.choices, default=UnidadMedida.UNIDAD)
    stockActual = models.DecimalField('Stock actual', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    stockMinimo = models.DecimalField('Stock mínimo', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    precioCosto = models.DecimalField('Precio de costo (₲)', max_digits=14, decimal_places=2, default=Decimal('0.00'))
    categoria = models.CharField('Categoría', max_length=80, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'material'
        verbose_name_plural = 'materiales'
        ordering = ['nombreMaterial']

    def __str__(self):
        return f"{self.codigo} - {self.nombreMaterial}"

    # Compatibilidad y aliases
    @property
    def descripcion(self):
        return self.nombreMaterial

    @property
    def unidad(self):
        return self.get_unidadMedida_display()

    @property
    def stock(self):
        return self.stockActual

    @property
    def stock_minimo(self):
        return self.stockMinimo

    @property
    def precio_costo(self):
        return self.precioCosto

    @property
    def stock_bajo(self):
        return self.esStockCritico()

    @property
    def valor_stock(self):
        return self.stockActual * self.precioCosto

    # Regla 6: esStockCritico() es verdadero cuando stockActual <= stockMinimo, y el stock nunca puede quedar negativo
    def esStockCritico(self):
        return self.stockActual <= self.stockMinimo


class PrecioProveedorMaterial(models.Model):
    """Clase de asociación Proveedor–Material con precio unitario y vigencia."""
    idPrecio = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='precios_materiales')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='precios_proveedores')
    precioUnitario = models.DecimalField('Precio unitario', max_digits=14, decimal_places=2)
    fechaActualizacion = models.DateField('Fecha de actualización', default=timezone.localdate)
    vigente = models.BooleanField('Vigente', default=True)

    class Meta:
        verbose_name = 'precio de proveedor por material'
        verbose_name_plural = 'precios de proveedores por materiales'

    def __str__(self):
        return f"{self.proveedor.razonSocial} - {self.material.nombreMaterial}: {self.precioUnitario}"

    def actualizarPrecio(self, precio):
        self.precioUnitario = Decimal(str(precio))
        self.fechaActualizacion = timezone.localdate()
        self.save()


class Presupuesto(models.Model):
    idPresupuesto = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='presupuestos')
    fechaEmision = models.DateField('Fecha de emisión', default=timezone.localdate)
    estadoPresupuesto = models.CharField('Estado', max_length=20, choices=EstadoPresupuesto.choices, default=EstadoPresupuesto.PENDIENTE)
    costoManoObra = models.DecimalField('Costo de mano de obra', max_digits=14, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'presupuesto'
        verbose_name_plural = 'presupuestos'
        ordering = ['-idPresupuesto']

    def __str__(self):
        return f"Presupuesto #{self.idPresupuesto:05d} - {self.cliente}"

    # Regla 2: /montoTotal = Σ subtotales + costoManoObra + costoFlete. El flete solo se suma si la modalidadEntrega es DOMICILIO.
    def calcularMontoTotal(self):
        subtotales = sum((d.subtotal for d in self.detalles.all()), Decimal('0.00'))
        flete = Decimal('0.00')
        if hasattr(self, 'entrega') and self.entrega.modalidadEntrega == ModalidadEntrega.DOMICILIO:
            flete = self.entrega.costoFlete or Decimal('0.00')
        return subtotales + self.costoManoObra + flete

    @property
    def montoTotal(self):
        return self.calcularMontoTotal()

    # Regla 3: /montoSena = montoTotal × 0.5, y el Pago de tipo SENA debe ser exactamente ese monto.
    def calcularSena(self):
        return (self.montoTotal * Decimal('0.5')).quantize(Decimal('0.01'))

    @property
    def montoSena(self):
        return self.calcularSena()

    @property
    def montoPagado(self):
        return sum((p.montoPago for p in self.pagos.all()), Decimal('0.00'))

    # Regla 5: /saldoPendiente = montoTotal − Σ pagos del presupuesto.
    @property
    def saldoPendiente(self):
        return self.montoTotal - self.montoPagado

    def agregarDetalle(self, detalle):
        detalle.presupuesto = self
        detalle.save()

    def aprobar(self):
        self.estadoPresupuesto = EstadoPresupuesto.APROBADO
        self.save(update_fields=['estadoPresupuesto'])

    def rechazar(self):
        self.estadoPresupuesto = EstadoPresupuesto.RECHAZADO
        self.save(update_fields=['estadoPresupuesto'])


class DetallePresupuesto(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='detalles')
    descripcionMueble = models.CharField('Descripción del mueble', max_length=200)
    largo = models.DecimalField('Largo (m)', max_digits=8, decimal_places=2, default=Decimal('0.00'))
    ancho = models.DecimalField('Ancho (m)', max_digits=8, decimal_places=2, default=Decimal('0.00'))
    alto = models.DecimalField('Alto (m)', max_digits=8, decimal_places=2, default=Decimal('0.00'))
    detalleMedidas = models.TextField(
        'Detalle de medidas y características',
        blank=True
    )
    colorTerminacion = models.CharField('Color / Terminación', max_length=100, blank=True)
    cantidad = models.PositiveIntegerField('Cantidad', default=1)
    margen = models.DecimalField('Margen de ganancia', max_digits=14, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'detalle de presupuesto'
        verbose_name_plural = 'detalles de presupuesto'

    def __str__(self):
        return f"{self.descripcionMueble} (Cant: {self.cantidad})"

    # Regla 1: El /subtotal de cada DetallePresupuesto es el costo de los materiales requeridos × cantidad (más margen, si se define).
    def calcularSubtotal(self):
        costo_materiales = sum(
            (req.cantidadRequerida * req.material.precioCosto for req in self.materiales_requeridos.all()),
            Decimal('0.00')
        )
        return (costo_materiales * self.cantidad) + self.margen

    @property
    def subtotal(self):
        return self.calcularSubtotal()


class MaterialRequerido(models.Model):
    """Clase de asociación DetallePresupuesto–Material."""
    idMaterialRequerido = models.AutoField(primary_key=True)
    detallePresupuesto = models.ForeignKey(DetallePresupuesto, on_delete=models.CASCADE, related_name='materiales_requeridos')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='requerimientos')
    cantidadRequerida = models.DecimalField('Cantidad requerida', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'material requerido'
        verbose_name_plural = 'materiales requeridos'

    def __str__(self):
        return f"{self.material.nombreMaterial} ({self.cantidadRequerida} {self.material.get_unidadMedida_display()})"

    def verificarDisponibilidad(self):
        return self.material.stockActual >= self.cantidadRequerida


class Entrega(models.Model):
    idEntrega = models.AutoField(primary_key=True)
    presupuesto = models.OneToOneField(Presupuesto, on_delete=models.CASCADE, related_name='entrega')
    modalidadEntrega = models.CharField('Modalidad de entrega', max_length=20, choices=ModalidadEntrega.choices, default=ModalidadEntrega.RETIRO_TALLER)
    direccionEntrega = models.CharField('Dirección de entrega', max_length=200, blank=True)
    costoFlete = models.DecimalField('Costo de flete', max_digits=14, decimal_places=2, default=Decimal('0.00'))
    observaciones = models.TextField('Observaciones', blank=True)

    class Meta:
        verbose_name = 'entrega'
        verbose_name_plural = 'entregas'

    def __str__(self):
        return f"{self.get_modalidadEntrega_display()} - {self.presupuesto}"


class Adjunto(models.Model):
    idAdjunto = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='adjuntos')
    tipoArchivo = models.CharField('Tipo de archivo', max_length=50)
    urlArchivo = models.CharField('URL o ruta del archivo', max_length=300)
    observaciones = models.TextField('Observaciones', blank=True)
    fechaSubida = models.DateField('Fecha de subida', default=timezone.localdate)

    class Meta:
        verbose_name = 'adjunto'
        verbose_name_plural = 'adjuntos'

    def __str__(self):
        return f"Adjunto #{self.idAdjunto} ({self.tipoArchivo})"

    def subirArchivo(self):
        pass

    def eliminarArchivo(self):
        self.delete()

    def obtenerVistaPrevia(self):
        return self.urlArchivo


class Pedido(models.Model):
    idPedido = models.AutoField(primary_key=True)
    presupuesto = models.OneToOneField(Presupuesto, on_delete=models.PROTECT, related_name='pedido')
    responsable = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pedidos_asignados')
    fechaRecepcion = models.DateField('Fecha de recepción', default=timezone.localdate)
    fechaEntregaEstimada = models.DateField('Fecha de entrega estimada')
    fechaEntregaReal = models.DateField('Fecha de entrega real', null=True, blank=True)
    estadoPedido = models.CharField('Estado del pedido', max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE)

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-idPedido']

    def __str__(self):
        return f"Pedido #{self.idPedido:05d} - {self.presupuesto.cliente.obtenerNombreCompleto()}"

    # Propiedades para compatibilidad con vistas / templates
    @property
    def numero(self):
        return self.idPedido

    @property
    def cliente(self):
        return self.presupuesto.cliente

    @property
    def descripcion(self):
        detalles = self.presupuesto.detalles.all()
        if detalles.exists():
            return ", ".join(d.descripcionMueble for d in detalles)
        return f"Trabajo Presupuesto #{self.presupuesto.idPresupuesto}"

    @property
    def madera(self):
        detalles = self.presupuesto.detalles.all()
        if detalles.exists():
            return detalles.first().colorTerminacion or "Estándar"
        return "Estándar"

    @property
    def fecha_entrega(self):
        return self.fechaEntregaEstimada

    @property
    def saldo(self):
        return self.presupuesto.saldoPendiente

    @property
    def total(self):
        return self.presupuesto.montoTotal

    @property
    def estado(self):
        return self.estadoPedido

    # Regla 4: El Pedido se crea solo cuando el Presupuesto está APROBADO y la seña fue pagada.
    @classmethod
    def crearDesdePresupuesto(cls, presupuesto, responsable, fechaEntregaEstimada, fechaRecepcion=None):
        if presupuesto.estadoPresupuesto != EstadoPresupuesto.APROBADO:
            raise ValidationError("El Pedido se crea solo cuando el Presupuesto está APROBADO.")
        if presupuesto.montoPagado < presupuesto.montoSena:
            raise ValidationError(
                f"La seña debe estar pagada para crear el pedido. Pagado: {presupuesto.montoPagado}, Seña requerida: {presupuesto.montoSena}."
            )
        pedido = cls(
            presupuesto=presupuesto,
            responsable=responsable,
            fechaRecepcion=fechaRecepcion or timezone.localdate(),
            fechaEntregaEstimada=fechaEntregaEstimada,
            estadoPedido=EstadoPedido.PENDIENTE
        )
        pedido.save()
        return pedido

    # Regla 8: Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.
    def clean(self):
        if self.pk:
            previo = Pedido.objects.get(pk=self.pk)
            if self.estadoPedido == EstadoPedido.ENTREGADO and previo.estadoPedido != EstadoPedido.TERMINADO:
                raise ValidationError("Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.")

    def actualizarEstado(self, estado):
        if estado == EstadoPedido.ENTREGADO and self.estadoPedido != EstadoPedido.TERMINADO:
            raise ValidationError("Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.")
        self.estadoPedido = estado
        if estado == EstadoPedido.ENTREGADO and not self.fechaEntregaReal:
            self.fechaEntregaReal = timezone.localdate()
        self.save()

    def asignarResponsable(self, usuario):
        self.responsable = usuario
        self.save(update_fields=['responsable'])

    def verificarStockDisponible(self):
        for detalle in self.presupuesto.detalles.all():
            for req in detalle.materiales_requeridos.all():
                if not req.verificarDisponibilidad():
                    return False
        return True


class Pago(models.Model):
    idPago = models.AutoField(primary_key=True)
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='pagos')
    fechaPago = models.DateField('Fecha de pago', default=timezone.localdate)
    montoPago = models.DecimalField('Monto del pago', max_digits=14, decimal_places=2)
    medioPago = models.CharField('Medio de pago', max_length=20, choices=MedioPago.choices, default=MedioPago.EFECTIVO)
    tipoPago = models.CharField('Tipo de pago', max_length=20, choices=TipoPago.choices, default=TipoPago.PARCIAL)
    nroComprobante = models.CharField('Nro. comprobante', max_length=50, blank=True)

    class Meta:
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'
        ordering = ['-idPago']

    def __str__(self):
        return f"Pago #{self.idPago} - {self.get_tipoPago_display()} - ₲ {self.montoPago}"

    # Regla 3: /montoSena = montoTotal × 0.5, y el Pago de tipo SENA debe ser exactamente ese monto.
    def validarMontoSena(self):
        if self.tipoPago == TipoPago.SENA:
            sena_esperada = self.presupuesto.montoSena
            return abs(self.montoPago - sena_esperada) <= Decimal('0.01')
        return True

    def clean(self):
        if self.tipoPago == TipoPago.SENA and not self.validarMontoSena():
            raise ValidationError(
                f"El Pago de tipo SENA debe ser exactamente el 50% del monto total (₲ {self.presupuesto.montoSena})."
            )

    def procesarPago(self):
        self.clean()
        self.save()

    def generarComprobantePDF(self):
        return f"comprobante_pago_{self.idPago}.pdf"


# Regla 10: Las compras de materiales se registran solo con Compra y PagoProveedor, no como GastoOperativo, para evitar doble conteo en caja.
class GastoOperativo(models.Model):
    idGasto = models.AutoField(primary_key=True)
    fechaGasto = models.DateField('Fecha del gasto', default=timezone.localdate)
    conceptoGasto = models.CharField('Concepto del gasto', max_length=200)
    montoGasto = models.DecimalField('Monto del gasto', max_digits=14, decimal_places=2)
    comprobanteRef = models.CharField('Comprobante de referencia', max_length=50, blank=True)

    class Meta:
        verbose_name = 'gasto operativo'
        verbose_name_plural = 'gastos operativos'
        ordering = ['-fechaGasto']

    def __str__(self):
        return f"{self.fechaGasto} - {self.conceptoGasto}: {self.montoGasto}"

    def registrarGasto(self):
        self.save()

    @classmethod
    def obtenerResumenGastos(cls, fecha_desde=None, fecha_hasta=None):
        qs = cls.objects.all()
        if fecha_desde:
            qs = qs.filter(fechaGasto__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fechaGasto__lte=fecha_hasta)
        return sum((g.montoGasto for g in qs), Decimal('0.00'))


class Compra(models.Model):
    idCompra = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    fechaCompra = models.DateField('Fecha de compra', default=timezone.localdate)

    class Meta:
        verbose_name = 'compra'
        verbose_name_plural = 'compras'
        ordering = ['-idCompra']

    def __str__(self):
        return f"Compra #{self.idCompra} - {self.proveedor.razonSocial}"

    def calcularTotal(self):
        return sum((d.subtotal for d in self.detalles.all()), Decimal('0.00'))

    @property
    def total(self):
        return self.calcularTotal()

    @property
    def saldoPendiente(self):
        pagos = sum((p.montoPago for p in self.pagos.all()), Decimal('0.00'))
        return self.total - pagos

    # Regla 7: Cada entrada de una Compra genera un MovimientoInventario de tipo ENTRADA.
    def registrarCompra(self):
        self.save()
        for detalle in self.detalles.all():
            movimiento = MovimientoInventario(
                material=detalle.material,
                compra=self,
                fechaMovimiento=self.fechaCompra,
                tipoMovimiento=TipoMovimiento.ENTRADA,
                cantidadMovimiento=detalle.cantidad,
                motivoObservacion=f"Entrada automática por Compra #{self.idCompra}"
            )
            movimiento.registrar()


class DetalleCompra(models.Model):
    idDetalleCompra = models.AutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='detalles_compra')
    cantidad = models.DecimalField('Cantidad', max_digits=12, decimal_places=2)
    precioUnitario = models.DecimalField('Precio unitario', max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'detalle de compra'
        verbose_name_plural = 'detalles de compra'

    def __str__(self):
        return f"{self.material.nombreMaterial} x {self.cantidad}"

    def calcularSubtotal(self):
        return self.cantidad * self.precioUnitario

    @property
    def subtotal(self):
        return self.calcularSubtotal()


class PagoProveedor(models.Model):
    idPagoProveedor = models.AutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='pagos')
    fechaPago = models.DateField('Fecha de pago', default=timezone.localdate)
    montoPago = models.DecimalField('Monto del pago', max_digits=14, decimal_places=2)
    medioPago = models.CharField('Medio de pago', max_length=20, choices=MedioPago.choices, default=MedioPago.TRANSFERENCIA)

    class Meta:
        verbose_name = 'pago a proveedor'
        verbose_name_plural = 'pagos a proveedores'
        ordering = ['-fechaPago']

    def __str__(self):
        return f"Pago #{self.idPagoProveedor} a Compra #{self.compra.idCompra}: {self.montoPago}"

    def registrarPago(self):
        self.save()


class CierreCaja(models.Model):
    idCierre = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='cierres_caja')
    fechaCierre = models.DateField('Fecha de cierre', default=timezone.localdate, unique=True)

    class Meta:
        verbose_name = 'cierre de caja'
        verbose_name_plural = 'cierres de caja'
        ordering = ['-fechaCierre']

    def __str__(self):
        return f"Cierre de caja {self.fechaCierre} por {self.usuario.username}"

    def calcularIngresosDiarios(self):
        return sum((p.montoPago for p in Pago.objects.filter(fechaPago=self.fechaCierre)), Decimal('0.00'))

    # Regla 10: Se suman gastos operativos y pagos a proveedores, excluyendo compras directas para evitar doble conteo
    def calcularEgresosDiarios(self):
        gastos = sum((g.montoGasto for g in GastoOperativo.objects.filter(fechaGasto=self.fechaCierre)), Decimal('0.00'))
        pagos_prov = sum((pp.montoPago for pp in PagoProveedor.objects.filter(fechaPago=self.fechaCierre)), Decimal('0.00'))
        return gastos + pagos_prov

    @property
    def totalIngresos(self):
        return self.calcularIngresosDiarios()

    @property
    def totalEgresos(self):
        return self.calcularEgresosDiarios()

    @property
    def balanceNeto(self):
        return self.totalIngresos - self.totalEgresos

    def exportarReportePDF(self):
        return f"cierre_caja_{self.fechaCierre}.pdf"


class MovimientoInventario(models.Model):
    idMovimiento = models.AutoField(primary_key=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='movimientos')
    pedido = models.ForeignKey(Pedido, null=True, blank=True, on_delete=models.SET_NULL, related_name='movimientos_inventario')
    compra = models.ForeignKey(Compra, null=True, blank=True, on_delete=models.SET_NULL, related_name='movimientos_inventario')
    fechaMovimiento = models.DateField('Fecha de movimiento', default=timezone.localdate)
    tipoMovimiento = models.CharField('Tipo de movimiento', max_length=20, choices=TipoMovimiento.choices)
    cantidadMovimiento = models.DecimalField('Cantidad', max_digits=12, decimal_places=2)
    motivoObservacion = models.CharField('Motivo u observación', max_length=200, blank=True)

    class Meta:
        verbose_name = 'movimiento de inventario'
        verbose_name_plural = 'movimientos de inventario'
        ordering = ['-idMovimiento']

    def __str__(self):
        return f"{self.get_tipoMovimiento_display()} {self.cantidadMovimiento} {self.material.nombreMaterial}"

    # Regla 6: esStockCritico() es verdadero cuando stockActual <= stockMinimo, y el stock nunca puede quedar negativo
    def registrar(self):
        if self.tipoMovimiento == TipoMovimiento.ENTRADA:
            self.material.stockActual += self.cantidadMovimiento
        elif self.tipoMovimiento in (TipoMovimiento.SALIDA_CONSUMO, TipoMovimiento.DESPERDICIO):
            if self.material.stockActual - self.cantidadMovimiento < Decimal('0.00'):
                raise ValidationError(
                    f"Stock insuficiente para {self.material.nombreMaterial}. El stock nunca puede quedar negativo."
                )
            self.material.stockActual -= self.cantidadMovimiento
        self.material.save(update_fields=['stockActual'])
        self.save()


# Regla 9: Las acciones críticas (pedidos, pagos, movimientos de materiales) generan un RegistroCambio automático.
class RegistroCambio(models.Model):
    idRegistro = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='registros_cambio')
    fechaHora = models.DateTimeField('Fecha y hora', default=timezone.now)
    entidad = models.CharField('Entidad afectada', max_length=50)
    idEntidad = models.IntegerField('ID de la entidad')
    accion = models.CharField('Acción realizada', max_length=20, choices=AccionAuditoria.choices)
    valorAnterior = models.TextField('Valor anterior', blank=True)
    valorNuevo = models.TextField('Valor nuevo', blank=True)

    class Meta:
        verbose_name = 'registro de cambio'
        verbose_name_plural = 'registros de cambios'
        ordering = ['-fechaHora']

    def __str__(self):
        return f"[{self.accion}] {self.entidad} #{self.idEntidad} a las {self.fechaHora}"

    @classmethod
    def consultarPorEntidad(cls, entidad, idEntidad=None):
        qs = cls.objects.filter(entidad=entidad)
        if idEntidad is not None:
            qs = qs.filter(idEntidad=idEntidad)
        return list(qs)


class Respaldo(models.Model):
    idRespaldo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='respaldos')
    fechaHora = models.DateTimeField('Fecha y hora', default=timezone.now)
    rutaArchivo = models.CharField('Ruta del archivo', max_length=300)
    tamanoMB = models.DecimalField('Tamaño (MB)', max_digits=8, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField('Estado', max_length=50, default='COMPLETADO')

    class Meta:
        verbose_name = 'respaldo'
        verbose_name_plural = 'respaldos'
        ordering = ['-fechaHora']

    def __str__(self):
        return f"Respaldo #{self.idRespaldo} ({self.tamanoMB} MB) - {self.estado}"


# ==============================================================================
# SIGNALS DE AUDITORÍA AUTOMÁTICA (Regla 9)
# ==============================================================================

@receiver(post_save, sender=Pedido)
def auditar_pedido(sender, instance, created, **kwargs):
    accion = AccionAuditoria.CREAR if created else AccionAuditoria.MODIFICAR
    RegistroCambio.objects.create(
        entidad='Pedido',
        idEntidad=instance.idPedido,
        accion=accion,
        valorNuevo=f"Estado: {instance.estadoPedido}, Resp: {instance.responsable.username}"
    )


@receiver(post_save, sender=Pago)
def auditar_pago(sender, instance, created, **kwargs):
    accion = AccionAuditoria.CREAR if created else AccionAuditoria.MODIFICAR
    RegistroCambio.objects.create(
        entidad='Pago',
        idEntidad=instance.idPago,
        accion=accion,
        valorNuevo=f"Tipo: {instance.tipoPago}, Monto: {instance.montoPago}, Presupuesto: #{instance.presupuesto.idPresupuesto}"
    )


@receiver(post_save, sender=MovimientoInventario)
def auditar_movimiento(sender, instance, created, **kwargs):
    accion = AccionAuditoria.CREAR if created else AccionAuditoria.MODIFICAR
    RegistroCambio.objects.create(
        entidad='MovimientoInventario',
        idEntidad=instance.idMovimiento,
        accion=accion,
        valorNuevo=f"Tipo: {instance.tipoMovimiento}, Cant: {instance.cantidadMovimiento}, Material: {instance.material.nombreMaterial}"
    )
