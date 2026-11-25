from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Categoria, Producto, Pedido, DetallePedido


COSTO_ENVIO_DOMICILIO = Decimal('25.00')


def _obtener_datos_carrito(request):
    """Construye la lista validada de ítems del carrito y calcula su subtotal."""
    carrito_sesion = request.session.get('carrito', {})
    items = []
    subtotal_general = Decimal('0.00')
    total_unidades = 0

    for prod_id_str, cantidad in list(carrito_sesion.items()):
        producto = Producto.objects.filter(id=int(prod_id_str), activo=True).first()
        if not producto or producto.existencias <= 0:
            del carrito_sesion[prod_id_str]
            request.session.modified = True
            continue

        if cantidad > producto.existencias:
            cantidad = producto.existencias
            carrito_sesion[prod_id_str] = cantidad
            request.session.modified = True

        subtotal_item = producto.precio * cantidad
        subtotal_general += subtotal_item
        total_unidades += cantidad

        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal_item,
            'alcanzo_maximo': cantidad >= producto.existencias,
        })

    return items, subtotal_general, total_unidades


def inicio(request):
    categorias = Categoria.objects.all()
    destacados = Producto.objects.filter(activo=True, destacado=True)[:4]
    return render(request, 'tienda/inicio.html', {
        'categorias': categorias,
        'destacados': destacados,
    })


def catalogo(request):
    categorias = Categoria.objects.all()
    productos = Producto.objects.filter(activo=True)

    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    solo_disponibles = request.GET.get('disponibles', '') == '1'

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if categoria_id.isdigit():
        productos = productos.filter(categoria_id=int(categoria_id))

    if precio_min:
        try:
            productos = productos.filter(precio__gte=Decimal(precio_min))
        except InvalidOperation:
            pass

    if precio_max:
        try:
            productos = productos.filter(precio__lte=Decimal(precio_max))
        except InvalidOperation:
            pass

    if solo_disponibles:
        productos = productos.filter(existencias__gt=0)

    contexto = {
        'categorias': categorias,
        'productos': productos,
        'busqueda': busqueda,
        'categoria_activa': int(categoria_id) if categoria_id.isdigit() else None,
        'precio_min': precio_min,
        'precio_max': precio_max,
        'solo_disponibles': solo_disponibles,
    }
    return render(request, 'tienda/catalogo.html', contexto)


def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    return render(request, 'tienda/detalle_producto.html', {
        'producto': producto,
    })


# =========================================================
# CARRITO DE COMPRAS (CU-06)
# =========================================================

def ver_carrito(request):
    items, subtotal_general, total_unidades = _obtener_datos_carrito(request)
    return render(request, 'tienda/carrito.html', {
        'items': items,
        'subtotal_general': subtotal_general,
        'total_unidades': total_unidades,
    })


def agregar_al_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('detalle_producto', producto_id=producto_id)

    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    if not producto.esta_disponible:
        messages.error(request, f'"{producto.nombre}" se encuentra agotado.')
        return redirect('detalle_producto', producto_id=producto.id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
        if cantidad < 1:
            cantidad = 1
    except ValueError:
        cantidad = 1

    carrito = request.session.get('carrito', {})
    prod_key = str(producto.id)
    cantidad_actual = carrito.get(prod_key, 0)
    nueva_cantidad = cantidad_actual + cantidad

    if nueva_cantidad > producto.existencias:
        carrito[prod_key] = producto.existencias
        messages.error(
            request,
            f'Solo hay {producto.existencias} unidades disponibles de "{producto.nombre}". Se ajustó al máximo disponible.'
        )
    else:
        carrito[prod_key] = nueva_cantidad
        messages.success(request, f'Se agregó "{producto.nombre}" a tu carrito.')

    request.session['carrito'] = carrito
    request.session.modified = True
    return redirect('ver_carrito')


def actualizar_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('ver_carrito')

    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    carrito = request.session.get('carrito', {})
    prod_key = str(producto.id)
    accion = request.POST.get('accion')

    if prod_key in carrito:
        cantidad_actual = carrito[prod_key]

        if accion == 'sumar':
            if cantidad_actual < producto.existencias:
                carrito[prod_key] = cantidad_actual + 1
            else:
                messages.error(
                    request,
                    f'Máximo disponible: {producto.existencias} unidades en existencia.'
                )
        elif accion == 'restar':
            if cantidad_actual > 1:
                carrito[prod_key] = cantidad_actual - 1
            else:
                del carrito[prod_key]

        request.session['carrito'] = carrito
        request.session.modified = True

    return redirect('ver_carrito')


def eliminar_del_carrito(request, producto_id):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        prod_key = str(producto_id)
        if prod_key in carrito:
            del carrito[prod_key]
            request.session['carrito'] = carrito
            request.session.modified = True
            messages.success(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


# =========================================================
# PROCESO DE COMPRA: ENTREGA, PAGO Y CONFIRMACIÓN (CU-07, CU-08, CU-09)
# =========================================================

@login_required(login_url='login')
def seleccionar_entrega(request):
    items, subtotal_general, total_unidades = _obtener_datos_carrito(request)
    if not items:
        messages.error(request, 'Tu carrito está vacío. Agrega productos antes de realizar un pedido.')
        return redirect('catalogo')

    datos_previos = request.session.get('checkout_entrega', {})
    metodo = datos_previos.get('metodo_entrega', 'DOMICILIO')
    direccion = datos_previos.get('direccion_entrega', '')
    referencia = datos_previos.get('referencia', '')
    telefono = datos_previos.get('telefono', '')
    errores = {}

    if request.method == 'POST':
        metodo = request.POST.get('metodo_entrega', 'DOMICILIO')
        direccion = request.POST.get('direccion_entrega', '').strip()
        referencia = request.POST.get('referencia', '').strip()
        telefono = request.POST.get('telefono', '').strip()

        if metodo not in ('DOMICILIO', 'RETIRO'):
            metodo = 'DOMICILIO'

        if metodo == 'DOMICILIO':
            if not direccion:
                errores['direccion'] = 'Ingresa la dirección completa de entrega.'
            if not telefono:
                errores['telefono'] = 'Ingresa un teléfono de contacto para el repartidor.'

        if not errores:
            costo_envio = COSTO_ENVIO_DOMICILIO if metodo == 'DOMICILIO' else Decimal('0.00')
            request.session['checkout_entrega'] = {
                'metodo_entrega': metodo,
                'direccion_entrega': direccion if metodo == 'DOMICILIO' else '12 Calle 4-55 Zona 1, Local 3 (Retiro en tienda)',
                'referencia': referencia if metodo == 'DOMICILIO' else '',
                'telefono': telefono,
                'costo_envio': str(costo_envio),
            }
            request.session.modified = True
            return redirect('procesar_pago')

    costo_envio_actual = COSTO_ENVIO_DOMICILIO if metodo == 'DOMICILIO' else Decimal('0.00')
    total_estimado = subtotal_general + costo_envio_actual

    return render(request, 'pedidos/entrega.html', {
        'items': items,
        'subtotal_general': subtotal_general,
        'costo_envio_domicilio': COSTO_ENVIO_DOMICILIO,
        'costo_envio_actual': costo_envio_actual,
        'total_estimado': total_estimado,
        'metodo': metodo,
        'direccion': direccion,
        'referencia': referencia,
        'telefono': telefono,
        'errores': errores,
    })


@login_required(login_url='login')
def procesar_pago(request):
    items, subtotal_general, total_unidades = _obtener_datos_carrito(request)
    if not items:
        return redirect('ver_carrito')

    datos_entrega = request.session.get('checkout_entrega')
    if not datos_entrega:
        return redirect('seleccionar_entrega')

    costo_envio = Decimal(datos_entrega.get('costo_envio', '0.00'))
    total_pagar = subtotal_general + costo_envio
    error_pasarela = None
    errores_campos = {}
    titular = request.user.get_full_name() or ''
    numero_tarjeta = ''
    expiracion = ''

    if request.method == 'POST':
        titular = request.POST.get('titular', '').strip()
        numero_tarjeta = request.POST.get('numero_tarjeta', '').replace(' ', '').strip()
        expiracion = request.POST.get('expiracion', '').strip()
        cvv = request.POST.get('cvv', '').strip()

        if not titular:
            errores_campos['titular'] = 'Ingresa el nombre del titular de la tarjeta.'
        if not numero_tarjeta.isdigit() or len(numero_tarjeta) < 13 or len(numero_tarjeta) > 19:
            errores_campos['numero_tarjeta'] = 'Ingresa un número de tarjeta válido (13 a 19 dígitos).'
        if len(expiracion) < 4:
            errores_campos['expiracion'] = 'Ingresa una fecha válida (MM/AA).'
        if not cvv.isdigit() or len(cvv) not in (3, 4):
            errores_campos['cvv'] = 'Código CVV inválido.'

        if not errores_campos:
            if numero_tarjeta.endswith('0000'):
                error_pasarela = {
                    'titulo': 'Pago rechazado por la pasarela',
                    'detalle': 'No se pudo procesar el cobro con los datos ingresados y no se realizó ningún cargo. Verifica tu tarjeta o intenta de nuevo.',
                }
            elif numero_tarjeta.endswith('9999'):
                error_pasarela = {
                    'titulo': 'La pasarela de pago no responde',
                    'detalle': 'No se pudo completar el cobro en este momento por tiempo de espera agotado. Intenta de nuevo en unos segundos.',
                }
            else:
                try:
                    with transaction.atomic():
                        for item in items:
                            prod_actual = Producto.objects.select_for_update().get(id=item['producto'].id)
                            if prod_actual.existencias < item['cantidad']:
                                raise ValueError(
                                    f'Existencias insuficientes para "{prod_actual.nombre}" (disponibles: {prod_actual.existencias}).'
                                )

                        pedido = Pedido.objects.create(
                            usuario=request.user,
                            metodo_entrega=datos_entrega['metodo_entrega'],
                            direccion_entrega=datos_entrega['direccion_entrega'],
                            referencia=datos_entrega.get('referencia', ''),
                            telefono=datos_entrega.get('telefono', ''),
                            subtotal=subtotal_general,
                            costo_envio=costo_envio,
                            total=total_pagar,
                            estado='PAGADO',
                            ultimos_digitos_tarjeta=numero_tarjeta[-4:],
                        )

                        for item in items:
                            prod_actual = Producto.objects.select_for_update().get(id=item['producto'].id)
                            DetallePedido.objects.create(
                                pedido=pedido,
                                producto=prod_actual,
                                cantidad=item['cantidad'],
                                precio_unitario=prod_actual.precio,
                            )
                            prod_actual.existencias -= item['cantidad']
                            prod_actual.save()

                    request.session['carrito'] = {}
                    request.session.pop('checkout_entrega', None)
                    request.session.modified = True

                    return redirect('confirmacion_pedido', pedido_id=pedido.id)

                except ValueError as err:
                    messages.error(request, str(err))
                    return redirect('ver_carrito')

    return render(request, 'pedidos/pago.html', {
        'items': items,
        'datos_entrega': datos_entrega,
        'subtotal_general': subtotal_general,
        'costo_envio': costo_envio,
        'total_pagar': total_pagar,
        'error_pasarela': error_pasarela,
        'errores_campos': errores_campos,
        'titular': titular,
        'numero_tarjeta': numero_tarjeta,
        'expiracion': expiracion,
    })


@login_required(login_url='login')
def confirmacion_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'pedidos/confirmacion.html', {
        'pedido': pedido,
        'detalles': pedido.detalles.select_related('producto').all(),
    })


# =========================================================
# SEGUIMIENTO E HISTORIAL DE PEDIDOS (CU-10)
# =========================================================

@login_required(login_url='login')
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-creado_en')
    return render(request, 'pedidos/mis_pedidos.html', {
        'pedidos': pedidos,
    })


@login_required(login_url='login')
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    orden_estados = ['PAGADO', 'PREPARACION', 'EN_CAMINO', 'ENTREGADO']
    indice_actual = orden_estados.index(pedido.estado) if pedido.estado in orden_estados else 0

    return render(request, 'pedidos/detalle_pedido.html', {
        'pedido': pedido,
        'detalles': pedido.detalles.select_related('producto').all(),
        'indice_actual': indice_actual,
    })


# =========================================================
# AUTENTICACIÓN (CU-01 Y CU-02)
# =========================================================

def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    errores = {}
    datos = {}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        datos = {'nombre': nombre, 'correo': correo}

        if not nombre:
            errores['nombre'] = 'Ingresa tu nombre completo.'

        if not correo:
            errores['correo'] = 'Ingresa un correo electrónico válido.'
        elif User.objects.filter(username=correo).exists() or User.objects.filter(email=correo).exists():
            errores['correo'] = 'Este correo electrónico ya está registrado. Intenta iniciar sesión o usa otro.'

        if len(password) < 8:
            errores['password'] = 'La contraseña es muy corta (debe tener al menos 8 caracteres).'

        if not errores:
            partes_nombre = nombre.split(' ', 1)
            first_name = partes_nombre[0]
            last_name = partes_nombre[1] if len(partes_nombre) > 1 else ''

            nuevo_usuario = User.objects.create_user(
                username=correo,
                email=correo,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, nuevo_usuario)
            messages.success(request, f'¡Bienvenido a Raíz Verde, {first_name}! Tu cuenta ha sido creada.')
            siguiente = request.GET.get('next')
            return redirect(siguiente if siguiente else 'inicio')

    return render(request, 'usuarios/registro.html', {'errores': errores, 'datos': datos})


def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    error_login = None
    correo = ''

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')

        usuario = authenticate(request, username=correo, password=password)

        if usuario is not None:
            login(request, usuario)
            if usuario.is_staff:
                return redirect('/admin/')
            siguiente = request.GET.get('next')
            return redirect(siguiente if siguiente else 'inicio')
        else:
            error_login = 'El correo electrónico o la contraseña son incorrectos. Verifica tus datos e intenta de nuevo.'

    return render(request, 'usuarios/login.html', {'error_login': error_login, 'correo': correo})


def logout_usuario(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')