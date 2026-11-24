from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


def inicio(request):
    return render(request, 'tienda/inicio.html')


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

        # Validación CU-01 flujo 4a: correo duplicado
        if not correo:
            errores['correo'] = 'Ingresa un correo electrónico válido.'
        elif User.objects.filter(username=correo).exists() or User.objects.filter(email=correo).exists():
            errores['correo'] = 'Este correo electrónico ya está registrado. Intenta iniciar sesión o usa otro.'

        # Validación CU-01 flujo 4b: contraseña corta
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
            # Si es administrador, lo llevamos directo a Django Admin (CU-02)
            if usuario.is_staff:
                return redirect('/admin/')
            siguiente = request.GET.get('next')
            return redirect(siguiente if siguiente else 'inicio')
        else:
            # Validación CU-02 flujo 4a: credenciales incorrectas
            error_login = 'El correo electrónico o la contraseña son incorrectos. Verifica tus datos e intenta de nuevo.'

    return render(request, 'usuarios/login.html', {'error_login': error_login, 'correo': correo})


def logout_usuario(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')