from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Categoria, Cliente, Material, OrdenTrabajo

MATERIALES = [
    # código, descripción, categoría, unidad, costo, stock, mínimo
    ('MAD-LAP', 'Lapacho cepillado 1" x 6"', 'Maderas', 'PT', 22000, 180, 100),
    ('MAD-CED', 'Cedro paraguayo 1" x 8"', 'Maderas', 'PT', 26000, 65, 80),
    ('MAD-PET', 'Peterevy 1" x 6"', 'Maderas', 'PT', 17000, 240, 100),
    ('MAD-INC', 'Incienso 2" x 4"', 'Maderas', 'PT', 19000, 40, 60),
    ('MAD-TIM', 'Timbó 1" x 10"', 'Maderas', 'PT', 14000, 120, 50),
    ('MAD-YVY', 'Yvyrapytã 1 1/2" x 6"', 'Maderas', 'PT', 18500, 95, 50),
    ('TAB-MDF18', 'MDF crudo 18 mm 1,83 x 2,60 m', 'Tableros', 'PL', 390000, 14, 6),
    ('TAB-MEL18', 'Melamina blanca 18 mm 1,83 x 2,60 m', 'Tableros', 'PL', 450000, 4, 8),
    ('TAB-TER3', 'Terciado 3 mm 1,22 x 2,44 m', 'Tableros', 'PL', 95000, 22, 10),
    ('HER-BIS35', 'Bisagra cazoleta 35 mm cierre suave', 'Herrajes', 'UN', 9500, 48, 60),
    ('HER-COR45', 'Corredera telescópica 45 cm (par)', 'Herrajes', 'UN', 38000, 30, 12),
    ('HER-TIR', 'Tirador de aluminio 128 mm', 'Herrajes', 'UN', 12000, 75, 30),
    ('INS-COLA', 'Cola vinílica 1 kg', 'Insumos', 'KG', 28000, 12, 6),
    ('INS-TOR40', 'Tornillo para madera 4 x 40 (caja x500)', 'Insumos', 'CJ', 45000, 3, 5),
    ('INS-LIJ120', 'Lija al agua grano 120', 'Insumos', 'UN', 4500, 150, 50),
    ('ACA-BAR', 'Barniz poliuretánico brillante 4 L', 'Acabados', 'LT', 165000, 5, 3),
    ('ACA-LAS', 'Laca nitro transparente 4 L', 'Acabados', 'LT', 140000, 2, 3),
]

CLIENTES = [
    ('Constructora Ñandutí S.A.', '80054321-0', 'Asunción'),
    ('Juan Carlos Benítez', '3456789', 'Luque'),
    ('Hotel Guaraní Palace', '80098765-2', 'Encarnación'),
    ('María González', '2987654', 'Fernando de la Mora'),
    ('Estudio Arq. Ramírez & Asoc.', '80033221-5', 'San Lorenzo'),
]

# cliente (índice), descripción, madera, estado, días desde hoy a la entrega, total, seña
TRABAJOS = [
    (0, 'Puertas placa x 12 para dúplex', 'Cedro', 'PRODUCCION', 5, 14_400_000, 7_200_000),
    (1, 'Mesa de comedor 8 personas', 'Lapacho', 'PRODUCCION', 3, 6_800_000, 3_400_000),
    (2, 'Placares empotrados x 6 habitaciones', 'MDF melamina', 'PRODUCCION', -2, 21_000_000, 10_500_000),
    (3, 'Cocina completa con alacenas', 'MDF melamina', 'TERMINADO', 1, 9_500_000, 5_000_000),
    (4, 'Escritorios para oficina x 4', 'Peterevy', 'PRESUPUESTO', 20, 5_600_000, 0),
    (1, 'Juego de sillas x 6', 'Lapacho', 'PRESUPUESTO', 25, 4_200_000, 0),
    (3, 'Rack para TV', 'Cedro', 'ENTREGADO', -10, 2_300_000, 2_300_000),
]


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para probar el sistema.'

    def handle(self, *args, **opciones):
        for codigo, desc, cat, unidad, costo, stock, minimo in MATERIALES:
            categoria, _ = Categoria.objects.get_or_create(nombre=cat)
            Material.objects.update_or_create(codigo=codigo, defaults={
                'descripcion': desc, 'categoria': categoria, 'unidad': unidad,
                'precio_costo': costo, 'stock': stock, 'stock_minimo': minimo,
            })

        clientes = [
            Cliente.objects.update_or_create(ruc=ruc, defaults={'razon_social': razon, 'ciudad': ciudad})[0]
            for razon, ruc, ciudad in CLIENTES
        ]

        if not OrdenTrabajo.objects.exists():
            hoy = timezone.localdate()
            for numero, (cli, desc, madera, estado, dias, total, sena) in enumerate(TRABAJOS, start=1):
                OrdenTrabajo.objects.create(
                    numero=numero, cliente=clientes[cli], descripcion=desc, madera=madera,
                    estado=estado, fecha_pedido=hoy - timedelta(days=15),
                    fecha_entrega=hoy + timedelta(days=dias), total=total, sena=sena,
                )

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados.'))
