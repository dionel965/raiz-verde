from django.contrib import admin
from .models import Categoria, Producto, Pedido, DetallePedido

admin.site.site_header = "Administración de Raíz Verde"
admin.site.site_title = "Raíz Verde Admin"
admin.site.index_title = "Panel de Gestión de la Tienda"


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'existencias', 'activo', 'destacado')
    list_filter = ('categoria', 'activo', 'destacado')
    search_fields = ('nombre', 'descripcion')
    # Permite editar existencias, activo y destacado directamente desde la lista (CU-12)
    list_editable = ('existencias', 'activo', 'destacado')

    fieldsets = (
        ('Información General del Producto', {
            'fields': ('nombre', 'categoria', 'precio', 'descripcion', 'imagen', 'existencias', 'activo', 'destacado')
        }),
        ('Cuidados de la Planta (Opcional)', {
            'fields': ('luz', 'riego', 'tamano'),
            'description': 'Complete estos campos únicamente si el producto es una planta.'
        }),
    )


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'precio_unitario')
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'usuario', 'creado_en', 'metodo_entrega', 'total', 'estado')
    list_filter = ('estado', 'metodo_entrega', 'creado_en')
    search_fields = ('codigo', 'usuario__username', 'usuario__email', 'usuario__first_name')
    inlines = [DetallePedidoInline]

    def get_readonly_fields(self, request, obj=None):
        campos_base = [
            'codigo', 'usuario', 'metodo_entrega', 'direccion_entrega',
            'referencia', 'telefono', 'subtotal', 'costo_envio',
            'total', 'ultimos_digitos_tarjeta', 'creado_en'
        ]
        # Si el pedido ya fue entregado, bloqueamos también el campo 'estado' (CU-13)
        if obj and obj.estado == 'ENTREGADO':
            return campos_base + ['estado']
        return campos_base  