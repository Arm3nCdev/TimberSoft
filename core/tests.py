from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.models import (
    Usuario,
    RolEnum,
    Cliente,
    Proveedor,
    Material,
    UnidadMedida,
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
    RegistroCambio,
)


class ReglasDeNegocioTestCase(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_test',
            password='123',
            rol=RolEnum.ADMIN,
            nombre='Admin',
            apellido='Test',
            ci='1111'
        )
        self.empleado = Usuario.objects.create_user(
            username='empleado_test',
            password='123',
            rol=RolEnum.EMPLEADO,
            nombre='Empleado',
            apellido='Test',
            ci='2222'
        )
        self.cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Pérez',
            ci='3333',
            rucCliente='3333-1',
            telefono='0981000000'
        )
        self.material = Material.objects.create(
            codigo='MAD-01',
            nombreMaterial='Cedro',
            unidadMedida=UnidadMedida.METRO,
            precioCosto=Decimal('10000.00'),
            stockActual=Decimal('50.00'),
            stockMinimo=Decimal('10.00')
        )
        self.proveedor = Proveedor.objects.create(
            rucProveedor='4444-1',
            razonSocial='Maderas S.A.'
        )

    # Regla 1: El /subtotal de cada DetallePresupuesto es el costo de los materiales requeridos × cantidad (más margen, si se define).
    def test_regla_1_subtotal_detalle_presupuesto(self):
        pres = Presupuesto.objects.create(cliente=self.cliente)
        det = DetallePresupuesto.objects.create(
            presupuesto=pres,
            descripcionMueble='Silla de cedro',
            cantidad=4,
            margen=Decimal('5000.00')
        )
        # 2 metros de cedro por silla = 2 * 10.000 = 20.000 de costo unitario
        MaterialRequerido.objects.create(
            detallePresupuesto=det,
            material=self.material,
            cantidadRequerida=Decimal('2.00')
        )
        # Subtotal = (20.000 * 4) + 5.000 = 85.000
        self.assertEqual(det.subtotal, Decimal('85000.00'))

    # Regla 2: /montoTotal = Σ subtotales + costoManoObra + costoFlete. El flete solo se suma si la modalidadEntrega es DOMICILIO.
    def test_regla_2_monto_total_con_y_sin_flete(self):
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('50000.00'))
        det = DetallePresupuesto.objects.create(presupuesto=pres, descripcionMueble='Mesa', cantidad=1, margen=Decimal('100000.00'))
        
        # Con RETIRO_TALLER no se suma el flete
        entrega = Entrega.objects.create(
            presupuesto=pres,
            modalidadEntrega=ModalidadEntrega.RETIRO_TALLER,
            costoFlete=Decimal('20000.00')
        )
        self.assertEqual(pres.montoTotal, Decimal('150000.00')) # 100.000 + 50.000 + 0

        # Cambiando a DOMICILIO sí se suma el flete
        entrega.modalidadEntrega = ModalidadEntrega.DOMICILIO
        entrega.save()
        self.assertEqual(pres.montoTotal, Decimal('170000.00')) # 100.000 + 50.000 + 20.000

    # Regla 3: /montoSena = montoTotal × 0.5, y el Pago de tipo SENA debe ser exactamente ese monto.
    def test_regla_3_monto_sena_exacto(self):
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'))
        self.assertEqual(pres.montoSena, Decimal('50000.00'))

        pago_invalido = Pago(
            presupuesto=pres,
            montoPago=Decimal('40000.00'), # No es el 50%
            tipoPago=TipoPago.SENA
        )
        with self.assertRaises(ValidationError):
            pago_invalido.clean()

        pago_valido = Pago(
            presupuesto=pres,
            montoPago=Decimal('50000.00'),
            tipoPago=TipoPago.SENA
        )
        pago_valido.clean() # Pasa validación sin error

    # Regla 4: El Pedido se crea solo cuando el Presupuesto está APROBADO y la seña fue pagada.
    def test_regla_4_creacion_pedido_valida_estado_y_sena(self):
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'))
        
        # Intento sin aprobar y sin pagar seña
        with self.assertRaises(ValidationError):
            Pedido.crearDesdePresupuesto(pres, self.empleado, timezone.localdate() + timezone.timedelta(days=5))

        # Aprobamos, pero aún falta pagar la seña
        pres.aprobar()
        with self.assertRaises(ValidationError):
            Pedido.crearDesdePresupuesto(pres, self.empleado, timezone.localdate() + timezone.timedelta(days=5))

        # Pagamos la seña completa
        pago = Pago(presupuesto=pres, montoPago=pres.montoSena, tipoPago=TipoPago.SENA)
        pago.procesarPago()

        # Ahora sí se crea correctamente
        pedido = Pedido.crearDesdePresupuesto(pres, self.empleado, timezone.localdate() + timezone.timedelta(days=5))
        self.assertIsNotNone(pedido.idPedido)

    # Regla 5: /saldoPendiente = montoTotal − Σ pagos del presupuesto.
    def test_regla_5_saldo_pendiente(self):
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('200000.00'))
        Pago.objects.create(presupuesto=pres, montoPago=Decimal('100000.00'), tipoPago=TipoPago.SENA)
        self.assertEqual(pres.saldoPendiente, Decimal('100000.00'))
        Pago.objects.create(presupuesto=pres, montoPago=Decimal('30000.00'), tipoPago=TipoPago.PARCIAL)
        self.assertEqual(pres.saldoPendiente, Decimal('70000.00'))

    # Regla 6: esStockCritico() es verdadero cuando stockActual <= stockMinimo, y el stock nunca puede quedar negativo.
    def test_regla_6_stock_critico_y_no_negativo(self):
        mat = Material.objects.create(
            codigo='MAD-02',
            nombreMaterial='Lapacho',
            unidadMedida=UnidadMedida.METRO,
            stockActual=Decimal('10.00'),
            stockMinimo=Decimal('10.00')
        )
        self.assertTrue(mat.esStockCritico())

        mat.stockActual = Decimal('15.00')
        self.assertFalse(mat.esStockCritico())

        # No puede quedar negativo al registrar salida
        mov = MovimientoInventario(
            material=mat,
            tipoMovimiento=TipoMovimiento.SALIDA_CONSUMO,
            cantidadMovimiento=Decimal('20.00') # Mayor al stock de 15
        )
        with self.assertRaises(ValidationError):
            mov.registrar()

    # Regla 7: Cada entrada de una Compra genera un MovimientoInventario de tipo ENTRADA.
    def test_regla_7_compra_genera_movimiento_entrada(self):
        compra = Compra.objects.create(proveedor=self.proveedor)
        DetalleCompra.objects.create(compra=compra, material=self.material, cantidad=Decimal('25.00'), precioUnitario=Decimal('9000.00'))
        
        stock_inicial = self.material.stockActual
        compra.registrarCompra()

        self.material.refresh_from_db()
        self.assertEqual(self.material.stockActual, stock_inicial + Decimal('25.00'))
        self.assertTrue(
            MovimientoInventario.objects.filter(compra=compra, tipoMovimiento=TipoMovimiento.ENTRADA).exists()
        )

    # Regla 8: Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.
    def test_regla_8_transicion_a_entregado(self):
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'), estadoPresupuesto=EstadoPresupuesto.APROBADO)
        Pago.objects.create(presupuesto=pres, montoPago=pres.montoSena, tipoPago=TipoPago.SENA)
        pedido = Pedido.crearDesdePresupuesto(pres, self.empleado, timezone.localdate())

        # Intento pasar directo de PENDIENTE a ENTREGADO -> Debe fallar
        with self.assertRaises(ValidationError):
            pedido.actualizarEstado(EstadoPedido.ENTREGADO)

        # Pasamos a TERMINADO y luego a ENTREGADO -> Válido
        pedido.actualizarEstado(EstadoPedido.TERMINADO)
        pedido.actualizarEstado(EstadoPedido.ENTREGADO)
        self.assertEqual(pedido.estadoPedido, EstadoPedido.ENTREGADO)

    # Regla 9: Las acciones críticas (pedidos, pagos, movimientos de materiales) generan un RegistroCambio automático.
    def test_regla_9_auditoria_automatica(self):
        # Pago
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'))
        pago = Pago.objects.create(presupuesto=pres, montoPago=Decimal('50000.00'), tipoPago=TipoPago.SENA)
        self.assertTrue(RegistroCambio.objects.filter(entidad='Pago', idEntidad=pago.idPago).exists())

        # Movimiento de inventario
        mov = MovimientoInventario.objects.create(
            material=self.material,
            tipoMovimiento=TipoMovimiento.ENTRADA,
            cantidadMovimiento=Decimal('5.00')
        )
        self.assertTrue(RegistroCambio.objects.filter(entidad='MovimientoInventario', idEntidad=mov.idMovimiento).exists())

    # Regla 10: Las compras de materiales se registran solo con Compra y PagoProveedor, no como GastoOperativo, para evitar doble conteo en caja.
    def test_regla_10_cierre_caja_calcula_sin_doble_conteo(self):
        hoy = timezone.localdate()
        # Pago de cliente = Ingreso 500.000
        pres = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('1000000.00'))
        Pago.objects.create(presupuesto=pres, fechaPago=hoy, montoPago=Decimal('500000.00'), tipoPago=TipoPago.SENA)

        # Gasto operativo = Egreso 100.000
        GastoOperativo.objects.create(fechaGasto=hoy, conceptoGasto='Luz', montoGasto=Decimal('100000.00'))

        # Compra con PagoProveedor = Egreso 150.000
        compra = Compra.objects.create(proveedor=self.proveedor, fechaCompra=hoy)
        PagoProveedor.objects.create(compra=compra, fechaPago=hoy, montoPago=Decimal('150000.00'))

        cierre = CierreCaja.objects.create(usuario=self.admin, fechaCierre=hoy)
        self.assertEqual(cierre.totalIngresos, Decimal('500000.00'))
        self.assertEqual(cierre.totalEgresos, Decimal('250000.00')) # 100.000 + 150.000
        self.assertEqual(cierre.balanceNeto, Decimal('250000.00')) # 500.000 - 250.000

    # Regla 11: Cada Pedido tiene un Usuario responsable. El EMPLEADO solo ve y actualiza los pedidos que tiene asignados; el ADMIN ve todos.
    def test_regla_11_responsable_y_permisos(self):
        pres1 = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'), estadoPresupuesto=EstadoPresupuesto.APROBADO)
        Pago.objects.create(presupuesto=pres1, montoPago=pres1.montoSena, tipoPago=TipoPago.SENA)
        ped_empleado = Pedido.crearDesdePresupuesto(pres1, self.empleado, timezone.localdate())

        pres2 = Presupuesto.objects.create(cliente=self.cliente, costoManoObra=Decimal('100000.00'), estadoPresupuesto=EstadoPresupuesto.APROBADO)
        Pago.objects.create(presupuesto=pres2, montoPago=pres2.montoSena, tipoPago=TipoPago.SENA)
        ped_admin = Pedido.crearDesdePresupuesto(pres2, self.admin, timezone.localdate())

        self.assertEqual(len(self.empleado.obtenerPedidosAsignados()), 1)
        self.assertEqual(self.empleado.obtenerPedidosAsignados()[0], ped_empleado)
        self.assertTrue(self.admin.validarPermiso('gestionar_compras'))
        self.assertFalse(self.empleado.validarPermiso('gestionar_compras'))
