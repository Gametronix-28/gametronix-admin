GAMETRONIX ADMIN PRO - ENVIOS USA CON ESTADOS

Mejora agregada:
- En Envíos USA ahora existe estado:
  1. Enviado
  2. Perdido
  3. Bodega Colombia

Regla:
- Al registrar un envío, el producto se descuenta de Bodega USA.
- Si queda en estado "Enviado", NO suma a Colombia todavía.
- Si queda en estado "Perdido", NO suma a Colombia.
- Solo cuando el estado sea "Bodega Colombia", el sistema suma automáticamente el producto a Bodega Colombia.
- Si ya entró a Bodega Colombia, no se puede cambiar a otro estado desde la pantalla normal; para corregir se debe anular el envío.

Usuario inicial:
admin

Contraseña:
admin123

Para abrir sin EXE:
ABRIR_APP_SIN_EXE.bat

Para crear EXE:
CREAR_EXE_WINDOWS.bat

El EXE queda en:
dist/GAMETRONIX_Admin_Pro_Envios.exe


NUEVO MÓDULO: GASTOS POR CAJA

- Gastos Colombia descuenta únicamente Caja Colombia en COP.
- Gastos USA descuenta únicamente Caja USA en USD.
- El módulo muestra saldos y tablas separadas.
- Al anular un gasto, el dinero vuelve automáticamente a la misma caja.


NUEVO: VENTA COLOMBIA CON SERIAL / NOTA

- La venta siempre descuenta producto desde Bodega Colombia.
- El valor total entra automáticamente a Caja Colombia.
- Ahora tiene campo de Serial del producto.
- También tiene Nota de venta.
- El historial de ventas muestra la columna notes con serial y observaciones.
- Al anular una venta, vuelve el stock a Bodega Colombia y se descuenta el dinero de Caja Colombia.


MEJORA: FACTURA COLOMBIA CON VARIOS PRODUCTOS

- Ahora Venta Colombia permite agregar hasta 10 productos en una misma factura.
- Cada producto tiene cantidad, precio, serial y nota individual.
- Al guardar, descuenta cada producto de Bodega Colombia.
- El total de la factura entra automáticamente a Caja Colombia.
- Se guarda factura principal y detalle por producto.
- En Borrar/anular registros puedes anular una factura completa: devuelve todos los productos al stock y resta el total de Caja Colombia.


MEJORA: VENTA COLOMBIA TIPO CARRITO

- Botón "Agregar producto a la factura": añade productos uno por uno.
- Cada producto puede tener serial y nota individual.
- Se puede quitar un producto o vaciar la factura antes de confirmar.
- Botón "Registrar venta": confirma la venta total.
- Al registrar la venta se descuenta Bodega Colombia y se suma el total a Caja Colombia.


DASHBOARD CORREGIDO DESDE BASE OFICIAL

- Se tomó como base el ZIP subido por el usuario: GAMETRONIX_Admin_Pro_Carrito_Factura(1).zip.
- El Dashboard de ganancias ahora suma las ventas de Colombia desde facturas múltiples.
- También mantiene compatibilidad con ventas directas antiguas si existen.
- Las métricas de ventas, costos, ganancia bruta y ganancia neta se actualizan con facturas registradas.
- Se agregó tabla de Facturas Colombia del período dentro del Dashboard.
- Se conserva el flujo de Venta Colombia tipo carrito: Agregar producto a la factura y Registrar venta.


MEDIOS DE PAGO Y BANCOS

- En Venta Colombia, si seleccionas Transferencia, aparece la opción para elegir banco/cuenta.
- Bancos disponibles: Bancolombia y Nequi.
- La factura guarda el medio de pago como "Transferencia - Bancolombia" o "Transferencia - Nequi".
- El Dashboard de ganancias ahora muestra el saldo recibido por cada medio de pago: Efectivo, Bancolombia, Nequi, Tarjeta y Otro.
- El resumen respeta el filtro de fecha del Dashboard: día, semana, mes o rango personalizado.


PDF POR FACTURA

- En Venta Colombia ahora aparece la sección "Generar PDF por factura".
- Al lado de cada factura puedes presionar "Generar PDF".
- El PDF incluye cliente, fecha, medio de pago, productos, cantidades, seriales, notas y total.
- El archivo queda listo para enviarlo al cliente por WhatsApp, correo o imprimirlo.
- Se agregó la dependencia reportlab para crear los PDF.


CORRECCION REPORTLAB

Si aparece el error:
ModuleNotFoundError: No module named 'reportlab'

Solución:
1. Ejecuta INSTALAR_DEPENDENCIAS.bat
2. Luego ejecuta ABRIR_APP_SIN_EXE.bat

Esta versión también corrige ABRIR_APP_SIN_EXE.bat para instalar reportlab automáticamente.


LIMPIEZA DASHBOARD Y VENTA COLOMBIA

- Se quitaron del Dashboard de ganancias:
  - cuadro/resumen de medios de pago
  - ventas directas antiguas del período
  - facturas Colombia del período
  - reparaciones del período
- En Venta Colombia se quitó la sección "Detalle de productos vendidos".
- Se conserva la lista de facturas y la opción para generar PDF por factura.


SIN CUADROS DE MEDIOS DE PAGO

- En el Dashboard se quitaron los cuadros grandes de Efectivo, Bancolombia, Nequi, Tarjeta y Otro.
- Se conserva únicamente la tabla/información de saldos por medio de pago.


TALLER AVANZADO

- Nueva orden de reparación con cliente, teléfono, equipo, serial, accesorios, estado recibido, falla, diagnóstico, solución, técnico y garantía.
- Permite usar repuestos desde Bodega Repuestos y los descuenta automáticamente del stock.
- Permite agregar repuestos comprados por fuera con costo, proveedor y nota.
- El costo de repuestos externos se suma al costo total y reduce la ganancia.
- Permite registrar abonos/pagos y saldos pendientes.
- Los abonos ingresan a Caja Colombia.
- Permite entregar equipo solo si no hay saldo pendiente.
- Incluye historial por cliente/teléfono/serial/equipo.
- Incluye PDF de orden de reparación.
- Al anular una reparación, devuelve repuestos de bodega, anula repuestos externos, anula pagos y descuenta de Caja Colombia lo pagado.


VERSIÓN LIMPIA CORREGIDA

Base usada: GAMETRONIX_Admin_Pro_Taller_Avanzado(1).zip

Correcciones aplicadas:
- Corrige payment_method_summary no definido.
- Corrige tabla faltante repair_external_parts.
- Corrige tablas faltantes repair_payments, invoices, invoice_items.
- Agrega migración automática al iniciar para bases de datos viejas.
- Mantiene módulos de taller avanzado y repuestos externos.
- Agrega BATs limpios para instalar dependencias y abrir la app.

Uso recomendado:
1. Ejecutar INSTALAR_DEPENDENCIAS.bat una vez.
2. Ejecutar ABRIR_APP_SIN_EXE.bat.
3. Si tienes datos anteriores, copia gametronix.db a esta carpeta antes de abrir.
