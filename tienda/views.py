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