# 🌿 Raíz Verde — Vivero Boutique & Tienda en Línea

Aplicación web de comercio electrónico desarrollada en **Django** para la venta de plantas de interior, plantas de exterior, macetas artesanales y accesorios de jardinería.

Proyecto desarrollado en colaboración internacional **COIL — UTP (Universidad Tecnológica de Panamá) × UVG (Universidad del Valle de Guatemala)**.

🖌 **Diseño inicial:** [https://www.figma.com/design/nzccReyHkwfPgv676EbV82/Tienda-de-plantas?node-id=0-1&t=mX7zZ5gu5KVsfAkP-1](https://www.figma.com/design/nzccReyHkwfPgv676EbV82/Tienda-de-plantas?node-id=0-1&t=mX7zZ5gu5KVsfAkP-1)  
🔗 **Sitio web en vivo:** [https://bayro79.pythonanywhere.com/](https://bayro79.pythonanywhere.com/)  
🔧 **Panel de Administración:** [https://bayro79.pythonanywhere.com/admin/](https://bayro79.pythonanywhere.com/admin/)

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Django 6
* **Frontend:** HTML5 (Plantillas Django), CSS3 (Diseño responsivo y variables personalizadas), JavaScript
* **Base de datos:** SQLite3
* **Gestión de imágenes:** Pillow
* **Despliegue en la nube:** PythonAnywhere

---

## 🔑 Credenciales de Prueba

El sistema incluye un comando automatizado (`cargar_datos`) que precarga categorías, productos, un pedido de muestra y los siguientes usuarios:

| Rol | Correo electrónico / Usuario | Contraseña | Acceso |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@raizverde.gt` | `admin1234` | Panel `/admin/` y gestión total |
| **Cliente** | `ana.morales@ejemplo.com` | `cliente1234` | Tienda, carrito, compras e historial |

---

## 📋 Funcionalidades y Casos de Uso Implementados (CU-01 a CU-13)

### Módulo del Cliente
* **CU-01 — Crear cuenta:** Registro de nuevos clientes con validación de correo único y longitud mínima de contraseña (8 caracteres).
* **CU-02 — Iniciar y cerrar sesión:** Autenticación de usuarios con redirección automática al panel administrativo para cuentas `staff`.
* **CU-03 — Explorar inicio y catálogo:** Portada con productos destacados, navegación por categorías y cuadrícula responsiva.
* **CU-04 — Buscar y filtrar productos:** Búsqueda por nombre/descripción y filtros combinables por categoría, rango de precios (Quetzales `Q`) y disponibilidad, incluyendo vista de *sin resultados*.
* **CU-05 — Ver detalle de producto:** Ficha completa con precio, existencias, sección condicional de cuidados (*luz, riego y tamaño*) para plantas y bloqueo de compra cuando el producto está agotado.
* **CU-06 — Gestionar carrito de compras:** Carrito persistente en sesión con ajuste de cantidades (`-` / `+`), control automático de existencias máximas, eliminación de productos y estado de carrito vacío.
* **CU-07 — Realizar pedido:** Resumen detallado de artículos, generación de código único (`#RV-YYYY-NNNN`), vaciado automático del carrito y comprobante de compra.
* **CU-08 — Seleccionar método de entrega:** Alternancia dinámica entre **Entrega a domicilio** (con formulario de dirección y recargo de envío de `Q25.00`) y **Retiro en tienda** (sin costo).
* **CU-09 — Realizar pago en línea:** Pasarela de pago simulada con tarjeta, validación de datos, manejo de escenarios de *pago rechazado* (`*0000`) o *pasarela sin respuesta* (`*9999`), y descuento transaccional de inventario.
* **CU-10 — Consultar historial y estado del pedido:** Vista *Mis pedidos* y detalle individual con barra de progreso en 4 etapas (*Pagado → En preparación → Listo para retiro / En camino → Entregado*).

### Módulo del Administrador (Django Admin)
* **CU-11 — Gestionar productos:** Creación, edición, activación/desactivación de productos y registro de cuidados botánicos.
* **CU-12 — Gestionar inventario:** Actualización rápida de existencias en tabla con validación de valores no negativos (`>= 0`).
* **CU-13 — Actualizar estado del pedido:** Seguimiento administrativo de pedidos recibidos con bloqueo automático de edición una vez marcados como *Entregado*.

---

## 📁 Estructura del Proyecto

```text
raiz-verde/
├── manage.py
├── requirements.txt
├── raiz_verde/                  # Configuración principal del proyecto Django
│   ├── settings.py
│   └── urls.py
├── tienda/                      # Aplicación principal (modelos, vistas, rutas, admin)
│   ├── management/
│   │   └── commands/
│   │       └── cargar_datos.py  # Script de carga de datos iniciales
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── templates/                   # Plantillas HTML organizadas por módulo
│   ├── base.html                # Plantilla base (barra de navegación y pie de página)
│   ├── tienda/                  # Inicio, catálogo, detalle de producto y carrito
│   ├── pedidos/                 # Entrega, pago, confirmación, mis pedidos y detalle
│   └── usuarios/                # Registro e inicio de sesión
├── static/                      # Archivos estáticos (hojas de estilo CSS)
│   └── css/
│       └── estilos.css
└── media/                       # Imágenes de productos subidas desde el panel admin
```

---

## 💻 Instalación y Ejecución Local

Si deseas clonar y ejecutar el proyecto en tu computadora:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/bayro79/raiz-verde.git
   cd raiz-verde
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Mac/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar migraciones y cargar datos de prueba:**
   ```bash
   python manage.py migrate
   python manage.py cargar_datos
   ```

5. **Iniciar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```
   Abre tu navegador en `http://127.0.0.1:8000/`.

---

## 🎨 Guía Rápida para Edición de Estilos (Frontend)

Para personalizar la apariencia visual sin afectar la lógica del sistema:
* Todos los estilos globales y de componentes están centralizados en **`static/css/estilos.css`**.
* Las plantillas HTML en **`templates/`** ya cuentan con las etiquetas de Django (`{% for %}`, `{% if %}`, `{{ variable }}`) y clases semánticas listas para ser estilizadas.
