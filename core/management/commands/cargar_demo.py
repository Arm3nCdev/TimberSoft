from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Usuario,
    RolEnum,
    Cliente,
    Proveedor,
    Material,
    UnidadMedida,
    PrecioProveedorMaterial,
    Presupuesto,
    EstadoPresupuesto,
    DetallePresupuesto,
    MaterialRequerido,
    Entrega,
    ModalidadEntrega,
    Pedido,
    EstadoPedido,
    Pago,
    TipoPago,
    MedioPago,
    Compra,
    DetalleCompra,
    PagoProveedor,
    MovimientoInventario,
    TipoMovimiento,
    GastoOperativo,
    CierreCaja,
)


class Command(BaseCommand):
    help = 'Carga datos de ejemplo demostrando todas las clases y reglas de negocio del OO de Carpintería Fabmag.'

    def handle(self, *args, **opciones):
        hoy = timezone.localdate()
        self.stdout.write('Iniciando carga de datos de demostración...')

        # 1. Usuarios
        admin, _ = Usuario.objects.get_or_create(
            username='admin',
            defaults={
                'nombre': 'Carlos',
                'apellido': 'Martínez',
                'ci': '1234567',
                'telefono': '0981111222',
                'direccion': 'Asunción',
                'rol': RolEnum.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'activo': True,
            }
        )
        admin.set_password('admin123')
        admin.save()

        empleado, _ = Usuario.objects.get_or_create(
            username='juan_taller',
            defaults={
                'nombre': 'Juan',
                'apellido': 'Benítez',
                'ci': '2345678',
                'telefono': '0982333444',
                'direccion': 'Carapeguá',
                'rol': RolEnum.EMPLEADO,
                'is_staff': False,
                'activo': True,
            }
        )
        empleado.set_password('empleado123')
        empleado.save()

        # 2. Proveedores
        prov_madera, _ = Proveedor.objects.get_or_create(
            rucProveedor='80011223-4',
            defaults={
                'razonSocial': 'Aserradero Santa Rosa S.R.L.',
                'rubroMaterial': 'Maderas nacionales nativas',
                'telefono': '0521200100',
                'direccion': 'Caaguazú Km 180',
            }
        )
        prov_herrajes, _ = Proveedor.objects.get_or_create(
            rucProveedor='80033445-1',
            defaults={
                'razonSocial': 'Ferretería Industrial del Este S.A.',
                'rubroMaterial': 'Herrajes, fijaciones y acabados',
                'telefono': '021555666',
                'direccion': 'Luque, Avda. Corrales',
            }
        )

        # 3. Materiales
        mats_data = [
            ('MAD-CED', 'Cedro paraguayo cepillado', UnidadMedida.METRO, Decimal('35000.00'), Decimal('120.00'), Decimal('80.00'), 'Maderas'),
            ('MAD-LAP', 'Lapacho para aberturas y pisos', UnidadMedida.METRO, Decimal('45000.00'), Decimal('40.00'), Decimal('60.00'), 'Maderas'), # crítico
            ('MAD-PET', 'Peterevy de primera', UnidadMedida.METRO, Decimal('32000.00'), Decimal('210.00'), Decimal('100.00'), 'Maderas'),
            ('TAB-MEL18', 'Melamina blanca 18 mm 1,83 x 2,60 m', UnidadMedida.M2, Decimal('95000.00'), Decimal('6.00'), Decimal('10.00'), 'Tableros'), # crítico
            ('HER-BIS35', 'Bisagra cazoleta 35 mm cierre suave', UnidadMedida.UNIDAD, Decimal('12000.00'), Decimal('50.00'), Decimal('40.00'), 'Herrajes'),
            ('HER-COR45', 'Corredera telescópica 45 cm (par)', UnidadMedida.UNIDAD, Decimal('42000.00'), Decimal('25.00'), Decimal('15.00'), 'Herrajes'),
            ('INS-COLA', 'Cola vinílica para carpintería', UnidadMedida.KG, Decimal('30000.00'), Decimal('15.00'), Decimal('8.00'), 'Insumos'),
            ('ACA-BAR', 'Barniz poliuretánico transparente', UnidadMedida.LITRO, Decimal('45000.00'), Decimal('2.00'), Decimal('5.00'), 'Acabados'), # crítico
        ]

        materiales = {}
        for cod, nom, unidad, costo, stock, smin, cat in mats_data:
            m, _ = Material.objects.update_or_create(
                codigo=cod,
                defaults={
                    'nombreMaterial': nom,
                    'unidadMedida': unidad,
                    'precioCosto': costo,
                    'stockActual': stock,
                    'stockMinimo': smin,
                    'categoria': cat,
                    'activo': True,
                }
            )
            materiales[cod] = m

        # 4. Precios de Proveedor
        PrecioProveedorMaterial.objects.get_or_create(
            proveedor=prov_madera,
            material=materiales['MAD-CED'],
            vigente=True,
            defaults={'precioUnitario': Decimal('33000.00'), 'fechaActualizacion': hoy}
        )
        PrecioProveedorMaterial.objects.get_or_create(
            proveedor=prov_herrajes,
            material=materiales['HER-BIS35'],
            vigente=True,
            defaults={'precioUnitario': Decimal('11000.00'), 'fechaActualizacion': hoy}
        )

        # 5. Clientes
        cli_nanduti, _ = Cliente.objects.get_or_create(
            rucCliente='80054321-0',
            defaults={
                'nombre': 'Constructora',
                'apellido': 'Ñandutí S.A.',
                'ci': '8005432',
                'telefono': '0981445566',
                'direccion': 'Asunción',
                'fechaRegistro': hoy - timedelta(days=60),
            }
        )
        cli_hotel, _ = Cliente.objects.get_or_create(
            rucCliente='80098765-2',
            defaults={
                'nombre': 'Hotel Guaraní',
                'apellido': 'Palace',
                'ci': '8009876',
                'telefono': '071203040',
                'direccion': 'Encarnación',
                'fechaRegistro': hoy - timedelta(days=30),
            }
        )
        cli_maria, _ = Cliente.objects.get_or_create(
            rucCliente='2987654-1',
            defaults={
                'nombre': 'María',
                'apellido': 'González',
                'ci': '2987654',
                'telefono': '0971556677',
                'direccion': 'Fernando de la Mora',
                'fechaRegistro': hoy - timedelta(days=15),
            }
        )

        # 6. Presupuesto 1 (Aprobado + Seña pagada -> Pedido en proceso)
        # Regla 1 (subtotal = materiales * cant + margen), Regla 2 (flete si DOMICILIO), Regla 3 (seña = 50%)
        pres1, created1 = Presupuesto.objects.get_or_create(
            cliente=cli_nanduti,
            costoManoObra=Decimal('1500000.00'),
            defaults={'fechaEmision': hoy - timedelta(days=10), 'estadoPresupuesto': EstadoPresupuesto.APROBADO}
        )
        if created1 or not pres1.detalles.exists():
            pres1.estadoPresupuesto = EstadoPresupuesto.APROBADO
            pres1.save()
            Entrega.objects.update_or_create(
                presupuesto=pres1,
                defaults={
                    'modalidadEntrega': ModalidadEntrega.DOMICILIO,
                    'direccionEntrega': 'Obra Villa Morra, Asunción',
                    'costoFlete': Decimal('300000.00'),
                }
            )
            det1 = DetallePresupuesto.objects.create(
                presupuesto=pres1,
                descripcionMueble='Puertas placa en cedro x 5',
                largo=Decimal('2.10'),
                ancho=Decimal('0.80'),
                alto=Decimal('0.04'),
                colorTerminacion='Cedro natural con laca',
                cantidad=5,
                margen=Decimal('500000.00')
            )
            MaterialRequerido.objects.create(detallePresupuesto=det1, material=materiales['MAD-CED'], cantidadRequerida=Decimal('15.00'))
            MaterialRequerido.objects.create(detallePresupuesto=det1, material=materiales['HER-BIS35'], cantidadRequerida=Decimal('3.00'))

            # Pago de la seña exacta del 50% (Regla 3)
            sena_exacta = pres1.montoSena
            pago_sena1 = Pago(
                presupuesto=pres1,
                fechaPago=hoy - timedelta(days=8),
                montoPago=sena_exacta,
                medioPago=MedioPago.TRANSFERENCIA,
                tipoPago=TipoPago.SENA,
                nroComprobante='TRANSF-9821'
            )
            pago_sena1.procesarPago()

            # Creación del pedido (Regla 4)
            Pedido.crearDesdePresupuesto(
                presupuesto=pres1,
                responsable=empleado,
                fechaEntregaEstimada=hoy + timedelta(days=4),
                fechaRecepcion=hoy - timedelta(days=8)
            )
            pres1.pedido.actualizarEstado(EstadoPedido.EN_PROCESO)

        # 7. Presupuesto 2 (Aprobado + Seña + Saldo parcial -> Pedido Terminado)
        pres2, created2 = Presupuesto.objects.get_or_create(
            cliente=cli_hotel,
            costoManoObra=Decimal('3000000.00'),
            defaults={'fechaEmision': hoy - timedelta(days=20), 'estadoPresupuesto': EstadoPresupuesto.APROBADO}
        )
        if created2 or not pres2.detalles.exists():
            pres2.estadoPresupuesto = EstadoPresupuesto.APROBADO
            pres2.save()
            Entrega.objects.update_or_create(
                presupuesto=pres2,
                defaults={
                    'modalidadEntrega': ModalidadEntrega.RETIRO_TALLER,
                    'direccionEntrega': '',
                    'costoFlete': Decimal('0.00'),
                }
            )
            det2 = DetallePresupuesto.objects.create(
                presupuesto=pres2,
                descripcionMueble='Placares empotrados en melamina x 2',
                largo=Decimal('2.40'),
                ancho=Decimal('2.00'),
                alto=Decimal('0.60'),
                colorTerminacion='Melamina blanca',
                cantidad=2,
                margen=Decimal('1000000.00')
            )
            MaterialRequerido.objects.create(detallePresupuesto=det2, material=materiales['TAB-MEL18'], cantidadRequerida=Decimal('8.00'))
            MaterialRequerido.objects.create(detallePresupuesto=det2, material=materiales['HER-COR45'], cantidadRequerida=Decimal('6.00'))

            # Pago Seña y Pago Parcial
            pago_sena2 = Pago(
                presupuesto=pres2,
                fechaPago=hoy - timedelta(days=18),
                montoPago=pres2.montoSena,
                medioPago=MedioPago.TRANSFERENCIA,
                tipoPago=TipoPago.SENA,
                nroComprobante='CHQ-5541'
            )
            pago_sena2.procesarPago()

            pedido2 = Pedido.crearDesdePresupuesto(
                presupuesto=pres2,
                responsable=admin,
                fechaEntregaEstimada=hoy + timedelta(days=1),
                fechaRecepcion=hoy - timedelta(days=18)
            )
            pedido2.actualizarEstado(EstadoPedido.TERMINADO)

        # 8. Presupuesto 3 (Completamente pagado y entregado -> Regla 8: pasa a ENTREGADO solo si previo TERMINADO)
        pres3, created3 = Presupuesto.objects.get_or_create(
            cliente=cli_maria,
            costoManoObra=Decimal('800000.00'),
            defaults={'fechaEmision': hoy - timedelta(days=25), 'estadoPresupuesto': EstadoPresupuesto.APROBADO}
        )
        if created3 or not pres3.detalles.exists():
            pres3.estadoPresupuesto = EstadoPresupuesto.APROBADO
            pres3.save()
            Entrega.objects.update_or_create(
                presupuesto=pres3,
                defaults={
                    'modalidadEntrega': ModalidadEntrega.DOMICILIO,
                    'direccionEntrega': 'Avda. Mcal. López c/ Zavala Cué',
                    'costoFlete': Decimal('150000.00'),
                }
            )
            det3 = DetallePresupuesto.objects.create(
                presupuesto=pres3,
                descripcionMueble='Rack para TV estilo nórdico',
                largo=Decimal('1.80'),
                ancho=Decimal('0.40'),
                alto=Decimal('0.60'),
                colorTerminacion='Peterevy y blanco',
                cantidad=1,
                margen=Decimal('400000.00')
            )
            MaterialRequerido.objects.create(detallePresupuesto=det3, material=materiales['MAD-PET'], cantidadRequerida=Decimal('6.00'))

            # Seña 50%
            pago_sena3 = Pago(
                presupuesto=pres3,
                fechaPago=hoy - timedelta(days=24),
                montoPago=pres3.montoSena,
                medioPago=MedioPago.EFECTIVO,
                tipoPago=TipoPago.SENA,
                nroComprobante='REC-001'
            )
            pago_sena3.procesarPago()

            pedido3 = Pedido.crearDesdePresupuesto(
                presupuesto=pres3,
                responsable=empleado,
                fechaEntregaEstimada=hoy - timedelta(days=2),
                fechaRecepcion=hoy - timedelta(days=24)
            )
            # Primero pasa a TERMINADO
            pedido3.actualizarEstado(EstadoPedido.TERMINADO)
            # Luego a ENTREGADO cumpliendo Regla 8
            pedido3.actualizarEstado(EstadoPedido.ENTREGADO)

            # Pago del Saldo total
            pago_saldo3 = Pago(
                presupuesto=pres3,
                fechaPago=hoy - timedelta(days=2),
                montoPago=pres3.saldoPendiente,
                medioPago=MedioPago.EFECTIVO,
                tipoPago=TipoPago.SALDO,
                nroComprobante='REC-002'
            )
            pago_saldo3.procesarPago()

        # 9. Presupuesto 4 (Pendiente de aprobación)
        pres4, created4 = Presupuesto.objects.get_or_create(
            cliente=cli_nanduti,
            costoManoObra=Decimal('2500000.00'),
            defaults={'fechaEmision': hoy - timedelta(days=1), 'estadoPresupuesto': EstadoPresupuesto.PENDIENTE}
        )
        if created4 or not pres4.detalles.exists():
            Entrega.objects.update_or_create(
                presupuesto=pres4,
                defaults={
                    'modalidadEntrega': ModalidadEntrega.DOMICILIO,
                    'direccionEntrega': 'Luque Obra Residencial',
                    'costoFlete': Decimal('200000.00'),
                }
            )
            DetallePresupuesto.objects.create(
                presupuesto=pres4,
                descripcionMueble='Juego de mesa de comedor y 6 sillas',
                largo=Decimal('2.20'),
                ancho=Decimal('1.00'),
                alto=Decimal('0.78'),
                colorTerminacion='Lapacho lustrado',
                cantidad=1,
                margen=Decimal('800000.00')
            )

        # 10. Compra de Materiales y Entradas automáticas de inventario (Regla 7)
        if not Compra.objects.exists():
            compra1 = Compra.objects.create(
                proveedor=prov_madera,
                fechaCompra=hoy - timedelta(days=5)
            )
            DetalleCompra.objects.create(
                compra=compra1,
                material=materiales['MAD-CED'],
                cantidad=Decimal('30.00'),
                precioUnitario=Decimal('33000.00')
            )
            # Regla 7: registrarCompra() genera MovimientoInventario ENTRADA
            compra1.registrarCompra()

            # Pago al proveedor
            PagoProveedor.objects.create(
                compra=compra1,
                fechaPago=hoy - timedelta(days=5),
                montoPago=Decimal('500000.00'),
                medioPago=MedioPago.TRANSFERENCIA
            )

        # 11. Movimiento adicional de Inventario y Salida por consumo (Regla 6)
        if not MovimientoInventario.objects.filter(tipoMovimiento=TipoMovimiento.SALIDA_CONSUMO).exists():
            mov_salida = MovimientoInventario(
                material=materiales['MAD-CED'],
                fechaMovimiento=hoy - timedelta(days=3),
                tipoMovimiento=TipoMovimiento.SALIDA_CONSUMO,
                cantidadMovimiento=Decimal('10.00'),
                motivoObservacion='Consumo para armado de marcos y bastidores'
            )
            mov_salida.registrar()

        # 12. Gasto Operativo (Regla 10: compras de materiales no se duplican como GastoOperativo)
        if not GastoOperativo.objects.exists():
            GastoOperativo.objects.create(
                fechaGasto=hoy,
                conceptoGasto='Servicio de energía eléctrica ANDE taller',
                montoGasto=Decimal('420000.00'),
                comprobanteRef='ANDE-FAC-1982'
            )
            GastoOperativo.objects.create(
                fechaGasto=hoy,
                conceptoGasto='Combustible para flete de entrega',
                montoGasto=Decimal('180000.00'),
                comprobanteRef='PETRO-8821'
            )

        # 13. Cierre de Caja
        CierreCaja.objects.get_or_create(
            fechaCierre=hoy,
            defaults={'usuario': admin}
        )

        self.stdout.write(self.style.SUCCESS('¡Datos de demostración cargados exitosamente según el Análisis Orientado a Objetos!'))
