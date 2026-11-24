from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tienda.models import Categoria, Producto, Pedido, DetallePedido


class Command(BaseCommand):
    help = "Carga categorías, productos, usuarios y pedidos de prueba para Raíz Verde"

    def handle(self, *args, **kwargs):
        # 1. Crear usuario Administrador
        admin_user, created = User.objects.get_or_create(
            username='admin@raizverde.gt',
            defaults={
                'email': 'admin@raizverde.gt',
                'first_name': 'Administrador',
                'last_name': 'Raíz Verde',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin1234')
            admin_user.save()

        # 2. Crear usuario Cliente de prueba
        cliente, created = User.objects.get_or_create(
            username='ana.morales@ejemplo.com',
            defaults={
                'email': 'ana.morales@ejemplo.com',
                'first_name': 'Ana Lucía',
                'last_name': 'Morales',
            }
        )
        if created:
            cliente.set_password('cliente1234')
            cliente.save()

        # 3. Crear Categorías
        nombres_cat = ['Interior', 'Exterior', 'Macetas', 'Tierra y abonos', 'Herramientas']
        cats = {}
        for nombre in nombres_cat:
            cats[nombre], _ = Categoria.objects.get_or_create(nombre=nombre)

        # 4. Crear Productos variados (disponibles, con cuidados, sin cuidados y agotados)
        productos_data = [
            {
                'nombre': 'Monstera deliciosa',
                'categoria': cats['Interior'],
                'precio': Decimal('125.00'),
                'descripcion': 'Planta tropical de hojas grandes y perforadas, ideal para dar frescura y estilo a salas o espacios luminosos.',
                'existencias': 8,
                'destacado': True,
                'luz': 'Luz indirecta brillante',
                'riego': '1 vez por semana',
                'tamano': '60 - 80 cm de altura',
            },
            {
                'nombre': 'Sansevieria Trifasciata',
                'categoria': cats['Interior'],
                'precio': Decimal('85.00'),
                'descripcion': 'Conocida como lengua de suegra. Muy resistente, purifica el aire y requiere cuidados mínimos.',
                'existencias': 15,
                'destacado': True,
                'luz': 'Luz baja a indirecta brillante',
                'riego': 'Cada 15 días',
                'tamano': '40 - 55 cm de altura',
            },
            {
                'nombre': 'Helecho Boston',
                'categoria': cats['Interior'],
                'precio': Decimal('95.00'),
                'descripcion': 'Follaje frondoso y arqueado perfecto para interiores húmedos o terrazas techadas.',
                'existencias': 6,
                'destacado': True,
                'luz': 'Sombra luminosa / luz filtrada',
                'riego': '2 a 3 veces por semana',
                'tamano': '35 - 50 cm de altura',
            },
            {
                'nombre': 'Lavanda Inglesa',
                'categoria': cats['Exterior'],
                'precio': Decimal('65.00'),
                'descripcion': 'Planta aromática de flores violetas resistente al sol directo, ideal para balcones y jardines.',
                'existencias': 10,
                'destacado': False,
                'luz': 'Sol directo (mínimo 6 horas)',
                'riego': '2 veces por semana',
                'tamano': '30 - 45 cm de altura',
            },
            {
                'nombre': 'Maceta de barro artesanal',
                'categoria': cats['Macetas'],
                'precio': Decimal('45.00'),
                'descripcion': 'Maceta de terracota natural hecha a mano con orificio de drenaje y plato base incluido.',
                'existencias': 0,  # Agotado para probar CU-05 y CU-12
                'destacado': True,
                'luz': '',
                'riego': '',
                'tamano': '',
            },
            {
                'nombre': 'Sustrato orgánico universal (5 kg)',
                'categoria': cats['Tierra y abonos'],
                'precio': Decimal('55.00'),
                'descripcion': 'Mezcla enriquecida con humus de lombriz, fibra de coco y perlita para un drenaje óptimo.',
                'existencias': 20,
                'destacado': False,
                'luz': '',
                'riego': '',
                'tamano': '',
            },
            {
                'nombre': 'Kit de herramientas de jardinería (3 piezas)',
                'categoria': cats['Herramientas'],
                'precio': Decimal('110.00'),
                'descripcion': 'Incluye pala trasplantadora, rastrillo de mano y cultivador con mango ergonómico de madera.',
                'existencias': 5,
                'destacado': False,
                'luz': '',
                'riego': '',
                'tamano': '',
            },
        ]

        productos_creados = []
        for data in productos_data:
            prod, _ = Producto.objects.get_or_create(
                nombre=data['nombre'],
                defaults=data
            )
            productos_creados.append(prod)

        # 5. Crear un pedido de ejemplo si aún no existen pedidos
        if not Pedido.objects.exists():
            pedido = Pedido.objects.create(
                usuario=cliente,
                metodo_entrega='DOMICILIO',
                direccion_entrega='4ta Avenida 12-30 Zona 10, Ciudad de Guatemala',
                referencia='Portón verde frente al parque',
                telefono='5512-3456',
                subtotal=Decimal('335.00'),
                costo_envio=Decimal('25.00'),
                total=Decimal('360.00'),
                estado='PREPARACION',
                ultimos_digitos_tarjeta='4532'
            )
            DetallePedido.objects.create(
                pedido=pedido,
                producto=productos_creados[0],  # 2x Monstera
                cantidad=2,
                precio_unitario=Decimal('125.00')
            )
            DetallePedido.objects.create(
                pedido=pedido,
                producto=productos_creados[1],  # 1x Sansevieria
                cantidad=1,
                precio_unitario=Decimal('85.00')
            )

        self.stdout.write(self.style.SUCCESS("¡Datos de prueba de Raíz Verde cargados exitosamente!"))
        self.stdout.write("  -> Admin:   admin@raizverde.gt / admin1234")
        self.stdout.write("  -> Cliente: ana.morales@ejemplo.com / cliente1234")