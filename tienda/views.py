from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Categoria, Producto


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

        # Ajustar si el stock en BD bajó respecto a lo guardado en sesión
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
            return redirect('inicio')

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