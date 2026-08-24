# 🍽️ ERP Gastronómico - Gestión Integral para Bares y Restaurantes

Sistema integral de gestión empresarial (ERP) desarrollado con **Python** y **Django** para optimizar la administración multi-sede, control de comandas en tiempo real (KDS), trazabilidad de inventarios con recetas dinámicas, caja y reportería financiera analítica.

---

## 🌟 Características Principales

### 🍸 Operación y Producción en Tiempo Real (KDS)
* **Comanda Digital para Clientes:** Menú interactivo parametrizado por sede y número de mesa con procesamiento de pedidos directo al sistema.
* **Estación de Cocina (Kitchen Display):** Pantalla en tiempo real para visualizar, preparar y despachar pedidos entrantes de cocina.
* **Estación de Barra (Bartender Dashboard):** Interfaz para coctelería y bebidas con actualización inmediata de estado de órdenes.

### 📦 Inventario, Insumos y Recetas Dinámicas
* **Gestión de Insumos y Unidades de Medida:** Control de inventario por sede, unidades de medida estandarizadas y umbrales de stock mínimo de seguridad.
* **Composición de Recetas (BOM):** Módulo de formulación de platos y cócteles con cálculo dinámico de cantidades requeridas de cada ingrediente.
* **Transformación y Procesamiento de Insumos:** Registro de movimientos y conversiones internas de materia prima a subrecetas.
* **Ingreso Masivo de Stock:** Interfaz y API para compras e ingresos rápidos de mercancía.

### 💰 Módulo de Caja y Gestión de Ventas
* **Arqueo y Control de Caja:** Apertura, cierre y registro de movimientos de caja por turno.
* **Múltiples Métodos de Pago:** Soporte para transacciones en efectivo, tarjetas y transferencias digitales.

### 📊 Reportes y Analítica Visual (Chart.js)
* **Métricas Semanales por Producto:** Seguimiento de volumen de preparación de platos y cócteles por semana seleccionada.
* **Distribución de Ingresos:** Gráficas de dona para analizar ventas por sede y métodos de pago.
* **Histórico Financiero y Rentabilidad:** Análisis comparativo de ingresos reales versus costo teórico de producción (márgenes de ganancia).
* **Mapa de Horas Pico:** Identificación de franjas horarias con mayor volumen de comandas para optimización del personal.

### 🏢 Multi-Sede y Seguridad Basada en Roles (RBAC)
* **Filtrado por Jerarquía:** Acceso global para usuarios con rol `OWNER` / Superusuarios y acceso restringido exclusivamente a la sucursal asignada para administradores locales (`ADMIN_SEDE`).
* **Modo Demo Interactivo:** Acceso transparente para evaluadores con mecanismo automatizado de restauración diaria de base de datos a medianoche vía GitHub Actions.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
| :--- | :--- |
| **Backend** | Python, Django, Gunicorn, WhiteNoise |
| **Frontend** | HTML5, Bootstrap 5, JavaScript (ES6+), Chart.js |
| **Base de Datos** | PostgreSQL (Supabase) / SQLite (Entorno local) |
| **Almacenamiento Multimedia** | Supabase Storage (Compatible con AWS S3 / django-storages) |
| **Despliegue & CI/CD** | Vercel (Serverless Functions), GitHub Actions (Cron Jobs) |

---

## 🚀 Instalación y Configuración Local

### 1. Clonar el Repositorio
```bash
git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
cd tu-repositorio/Backend-Frontend
```

### 2. Crear y Activar el Entorno Virtual
``` bash
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```
### 3. Instalar Dependencias
 ```bash
pip install -r requirements.txt
```
### 4. Configurar Variables de Entorno
Crea un archivo .env en la raíz de Backend-Frontend/ tomando como base la siguiente estructura:

``` code snippet
SECRET_KEY=tu_clave_secreta_de_django
DEBUG=True

# Base de datos (Supabase / PostgreSQL)
DB_NAME=postgres
DB_USER=postgres.tu_project_ref
DB_PASSWORD=tu_contrasena_supabase
DB_HOST=aws-0-tu-region.pooler.supabase.com
DB_PORT=6543

# Storage Multimedia (Supabase S3)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_STORAGE_BUCKET_NAME=tu_bucket
SUPABASE_PROJECT_ID=tu_project_id
```
### 5. Ejecutar Migraciones y Cargar Datos Semilla
``` bash
python manage.py migrate
python manage.py loaddata demo_seed.json
```
### 6. Iniciar el Servidor de Desarrollo
``` bash
python manage.py runserver
```

Accede a http://127.0.0.1:8000 en tu navegador.

## 📂 Estructura del Proyecto
``` code snippet
Plaintext
├── .github/
│   └── workflows/
│       └── reset_demo.yml       # Cron job diario para restaurar la DB demo
├── Backend-Frontend/
│   ├── core_erp/                # Configuración principal, settings, WSGI y urls
│   ├── inventory/               # Aplicación principal del ERP
│   │   ├── management/          # Comandos personalizados (reset_demo)
│   │   ├── models.py            # Modelos (Productos, Recetas, Sedes, Insumos)
│   │   ├── forms.py             # Formularios con sanitización y máscaras
│   │   └── views/               # Vistas modularizadas (Admin, Cocina, Barra, etc.)
│   ├── static/                  # Archivos estáticos (CSS, JS, iconos)
│   ├── templates/               # Plantillas HTML con Bootstrap 5
│   ├── demo_seed.json           # Fixture con el estado inicial de prueba
│   ├── manage.py
│   ├── requirements.txt
│   └── vercel.json              # Configuración de despliegue en Vercel
└── README.md
```
## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.