** Reglas de negocio **
1.--	El /subtotal de cada DetallePresupuesto es el costo de los materiales requeridos × cantidad (más margen, si se define).
2.--	/montoTotal = Σ subtotales + costoManoObra + costoFlete. El flete solo se suma si la modalidadEntrega es DOMICILIO.
3.--	/montoSena = montoTotal × 0.5, y el Pago de tipo SENA debe ser exactamente ese monto.
4.--	El Pedido se crea solo cuando el Presupuesto está APROBADO y la seña fue pagada.
5.--	/saldoPendiente = montoTotal − Σ pagos del presupuesto.
6.--	esStockCritico() es verdadero cuando stockActual <= stockMinimo, y el stock nunca puede quedar negativo.
7.--	Cada entrada de una Compra genera un MovimientoInventario de tipo ENTRADA.
8.--	Un Pedido pasa a ENTREGADO solo si su estado previo era TERMINADO.
9.--	Las acciones críticas (pedidos, pagos, movimientos de materiales) generan un RegistroCambio automático.
10.--	Las compras de materiales se registran solo con Compra y PagoProveedor, no como GastoOperativo, para evitar doble conteo en caja.
11.--	Cada Pedido tiene un Usuario responsable. El EMPLEADO solo ve y actualiza los pedidos que tiene asignados; el ADMIN ve todos.
