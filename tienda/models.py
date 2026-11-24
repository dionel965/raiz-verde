from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name="Categoría"
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (Q)")
    descripcion = models.TextField(verbose_name="Descripción")
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True,
        verbose_name="Imagen"
    )
    # PositiveIntegerField garantiza que las existencias sean >= 0 (CU-12)
    existencias = models.PositiveIntegerField(default=0, verbose_name="Existencias")
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desmarque esta casilla para desactivar el producto del catálogo."
    )
    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado en Inicio"
    )

    # Cuidados opcionales (solo aplican si el producto es una planta - CU-05 / CU-11)
    luz = models.CharField(max_length=100, blank=True, verbose_name="Luz")
    riego = models.CharField(max_length=100, blank=True, verbose_name="Riego")
    tamano = models.CharField(max_length=100, blank=True, verbose_name="Tamaño")

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def esta_disponible(self):
        return self.activo and self.existencias > 0

    @property
    def tiene_cuidados(self):
        return bool(self.luz or self.riego or self.tamano)


class Pedido(models.Model):
    ESTADOS = [
        ('PAGADO', 'Pagado'),
        ('PREPARACION', 'En preparación'),
        ('EN_CAMINO', 'Listo para retiro / En camino'),
        ('ENTREGADO', 'Entregado'),
    ]

    METODOS_ENTREGA = [
        ('DOMICILIO', 'Entrega a domicilio'),
        ('RETIRO', 'Retiro en tienda'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Número de pedido"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name="Cliente"
    )
    metodo_entrega = models.CharField(
        max_length=20,
        choices=METODOS_ENTREGA,
        default='DOMICILIO',
        verbose_name="Método de entrega"
    )
    direccion_entrega = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Dirección de entrega"
    )
    referencia = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Referencia adicional"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono de contacto"
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal (Q)")
    costo_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo de envío (Q)"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total (Q)")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PAGADO',
        verbose_name="Estado del pedido"
    )
    ultimos_digitos_tarjeta = models.CharField(
        max_length=4,
        default='4532',
        verbose_name="Terminación de tarjeta"
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.codigo} - {self.usuario.get_full_name() or self.usuario.username}"

    def clean(self):
        # Regla CU-13: Si el pedido ya estaba 'Entregado', no se puede cambiar de estado
        if self.pk:
            estado_anterior = Pedido.objects.get(pk=self.pk).estado
            if estado_anterior == 'ENTREGADO' and self.estado != 'ENTREGADO':
                raise ValidationError(
                    "Los pedidos en estado 'Entregado' quedan bloqueados y no permiten cambios posteriores."
                )

    def save(self, *args, **kwargs):
        if not self.codigo:
            anio = timezone.now().year
            ultimo_id = (Pedido.objects.order_by('-id').first().id if Pedido.objects.exists() else 0) + 1
            self.codigo = f"#RV-{anio}-{ultimo_id:04d}"
        super().save(*args, **kwargs)


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Pedido"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio unitario (Q)"
    )

    class Meta:
        verbose_name = "Artículo del pedido"
        verbose_name_plural = "Artículos del pedido"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario