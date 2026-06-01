# Sistema de Gestión Clínica — Tesis Web App

Aplicación web para la gestión de consultas clínicas, pacientes, profesionales y reportes con asistente IA. Construida con Django 4.2, Bootstrap 5 (Material Dashboard) y la API de OpenAI.

---

## Tabla de contenidos

- [Requisitos](#requisitos)
- [Configuración inicial](#configuración-inicial)
- [Levantar el servidor](#levantar-el-servidor)
- [Variables de entorno](#variables-de-entorno)
- [Base de datos](#base-de-datos)
- [Comandos útiles](#comandos-útiles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Módulos y rutas](#módulos-y-rutas)
- [Funcionalidad IA](#funcionalidad-ia)
- [Notas de despliegue](#notas-de-despliegue)

---

## Requisitos

- Python 3.12+
- pip
- PostgreSQL (producción) o SQLite (desarrollo local)
- Clave API de OpenAI (para el módulo de reportes IA)

---

## Configuración inicial

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd material-dashboard-django

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar el archivo de entorno y completar los valores
copy env.sample .env
# Editar .env con tus credenciales (ver sección Variables de entorno)

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear superusuario (admin)
python manage.py createsuperuser
```

---

## Levantar el servidor

```bash
# Desarrollo (recarga automática)
python manage.py runserver

# Puerto personalizado
python manage.py runserver 0.0.0.0:8080
```

Abre el navegador en **http://127.0.0.1:8000/**

---

## Variables de entorno

Copia `env.sample` a `.env` y rellena los campos:

```env
# Modo de depuración (True en desarrollo, False en producción)
DEBUG=True

# Clave secreta Django (genera una con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
SECRET_KEY=tu_clave_secreta_aqui

# Base de datos PostgreSQL (si no se define, usa SQLite por defecto)
DB_ENGINE=postgresql
DB_HOST=localhost
DB_NAME=nombre_base_datos
DB_USERNAME=usuario
DB_PASS=contraseña
DB_PORT=5432

# OpenAI (necesario para el módulo de reportes IA)
OPENAI_API_KEY=sk-proj-...

# Correo electrónico (para recuperación de contraseña)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
DEFAULT_FROM_EMAIL=noreply@tudominio.com
```

> Si `DB_ENGINE` no está definido, Django usa **SQLite** (`db.sqlite3`) automáticamente — útil para desarrollo local sin instalar PostgreSQL.

---

## Base de datos

```bash
# Aplicar todas las migraciones pendientes
python manage.py migrate

# Crear nuevas migraciones tras cambios en modelos
python manage.py makemigrations

# Ver el estado de las migraciones
python manage.py showmigrations

# Revertir a una migración específica
python manage.py migrate pages 0015
```

### Reset completo (desarrollo)

```bash
# Elimina la base SQLite y vuelve a migrar desde cero
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Comandos útiles

### Gestión de usuarios

```bash
# Crear superusuario
python manage.py createsuperuser

# Cambiar contraseña de un usuario existente
python manage.py changepassword oscar

# Abrir shell interactivo de Django
python manage.py shell
```

### Shell — operaciones comunes

```python
# Acceder al shell
python manage.py shell

# Listar todos los usuarios
from django.contrib.auth.models import User
User.objects.all()

# Resetear conversaciones IA de todos los threads
from apps.pages.models import PatientAIThread, PatientAIMessage
PatientAIMessage.objects.all().delete()
PatientAIThread.objects.all().update(openai_conversation_id='', context='', context_consult_count=0, context_note_count=0, context_attachment_count=0)

# Listar pacientes
from apps.pages.models import Patient
Patient.objects.all().values('id', 'first_name', 'last_name')
```

### Archivos estáticos

```bash
# Recolectar estáticos para producción
python manage.py collectstatic --no-input
```

### Verificación del proyecto

```bash
# Comprobar que no hay errores de configuración
python manage.py check

# Verificar migraciones sin aplicar
python manage.py migrate --check
```

---

## Estructura del proyecto

```
├── apps/
│   ├── pages/          # Módulo principal — pacientes, profesionales, citas, sesiones, IA
│   ├── finance/        # Módulo de finanzas
│   ├── charts/         # Gráficos con ApexCharts
│   ├── dyn_dt/         # DataTables dinámicas
│   └── dyn_api/        # APIs dinámicas
├── config/
│   ├── settings.py     # Configuración Django
│   ├── urls.py         # URLs raíz
│   └── wsgi.py
├── static/
│   ├── css/
│   │   └── custom-combo.css    # Widget combobox personalizado
│   └── js/
│       └── custom-combo.js     # Lógica del combobox
├── templates/
│   ├── layouts/        # Base templates (base.html, auth)
│   ├── pages/          # Vistas del sistema clínico
│   └── includes/       # Sidebar, footer
├── media/              # Archivos subidos (adjuntos de consultas, fotos de perfil)
├── manage.py
├── requirements.txt
└── .env                # Variables de entorno (no commitear)
```

---

## Módulos y rutas

| URL | Descripción |
|-----|-------------|
| `/` | Dashboard principal |
| `/accounts/login/` | Inicio de sesión |
| `/patients/` | Gestión de pacientes |
| `/professionals/` | Gestión de profesionales |
| `/parameters/` | Catálogo de especialidades y parámetros |
| `/consult/` | Gestión de citas (crear, cancelar, filtrar) |
| `/start-session/<id>/` | Workspace de sesión clínica (notas + adjuntos) |
| `/mis-pacientes/` | Vista de pacientes asignados al profesional |
| `/mis-pacientes/<id>/` | Historial clínico de un paciente |
| `/config/consultorios/` | Configuración de consultorios |
| `/config/consultorios/calendario/` | Calendario de consultorios |
| `/report/sessions/` | Reporte IA — resumen clínico y chat |
| `/report/sessions/pdf/` | Descarga del reporte en PDF |
| `/profile/` | Perfil del usuario (5 pestañas) |
| `/admin/` | Panel de administración Django |

---

## Funcionalidad IA

El módulo de **Reporte de Sesiones** usa la **Responses API de OpenAI** con **Conversations** para mantener el contexto del paciente de forma persistente entre mensajes.

### Flujo

1. Seleccionar paciente → clic en **"Generar Resumen"**
2. El sistema construye el contexto clínico (consultas, notas, adjuntos) y crea una **Conversation en OpenAI** (`conv_...`)
3. El ID de la conversación se guarda en `PatientAIThread.openai_conversation_id`
4. Cada pregunta en el chat pasa solo el mensaje nuevo — OpenAI gestiona el historial completo en el servidor
5. Los mensajes también se persisten localmente en `PatientAIMessage` para el PDF y la visualización

### Reset de conversaciones IA

Si necesitas empezar desde cero (p.ej. tras cambio de modelo):

```python
python manage.py shell
from apps.pages.models import PatientAIThread, PatientAIMessage
PatientAIMessage.objects.all().delete()
PatientAIThread.objects.all().update(openai_conversation_id='', context='', context_consult_count=0, context_note_count=0, context_attachment_count=0)
```

### Reprocesar adjuntos

Si los archivos del paciente no están subidos a OpenAI, usa el botón **"Reprocesar Adjuntos"** en la página de reporte, o mediante API:

```
POST /report/sessions/reupload/
patient=<id>
```

---

## Notas de despliegue

### Docker

```bash
docker-compose up --build
```

### Variables adicionales para producción

```env
DEBUG=False
SECRET_KEY=clave-larga-y-aleatoria
RENDER_EXTERNAL_HOSTNAME=tu-app.onrender.com
```

### Render

El archivo `render.yaml` contiene la configuración lista para desplegar en [Render](https://render.com). Conecta el repositorio y configura las variables de entorno en el dashboard de Render.

### Colectar estáticos antes de desplegar

```bash
python manage.py collectstatic --no-input
```

---

## Stack tecnológico

| Componente | Tecnología |
|------------|------------|
| Framework | Django 4.2.9 |
| Python | 3.12+ |
| UI | Bootstrap 5 + Material Dashboard |
| Base de datos | PostgreSQL (prod) / SQLite (dev) |
| IA | OpenAI Responses API + Conversations |
| PDF | xhtml2pdf |
| Íconos | Material Symbols Rounded |
| Servidor | Gunicorn + WhiteNoise |


 ![version](https://img.shields.io/badge/version-1.0.1-blue.svg) [![GitHub issues open](https://img.shields.io/github/issues/creativetimofficial/material-dashboard-django.svg?maxAge=2592000)](https://github.com/creativetimofficial/material-dashboard-django/issues?q=is%3Aopen+is%3Aissue) [![GitHub issues closed](https://img.shields.io/github/issues-closed-raw/creativetimofficial/material-dashboard-django.svg?maxAge=2592000)](https://github.com/creativetimofficial/material-dashboard-django/issues?q=is%3Aissue+is%3Aclosed) [![Join the chat at https://gitter.im/NIT-dgp/General](https://badges.gitter.im/NIT-dgp/General.svg)](https://gitter.im/creative-tim-general/Lobby) [![Chat](https://img.shields.io/badge/chat-on%20discord-7289da.svg)](https://discord.gg/E4aHAQy)

Open-source **[Django Template](https://www.creative-tim.com/templates/django)** built on top of **Material Dashboard**, a modern Bootstrap 5 design. Start your development with a modern Bootstrap 5 Admin template for Django. Soft UI Dashboard is built with over 70 individual components, giving you the freedom of choosing and combining. If you want to code faster, with a smooth workflow, then you should try this template carefully developed with Django, a well-known Python Framework.

> NOTE: Starter provided in partnership with [App-Generator](https://app-generator.dev/), an open-source platform for developers

<br />

## Features: 

- Simple, Easy-to-Extend Codebase
- Material Dashboard design Integration
- Bootstrap CSS Styling 
- Session-based Authentication, Password recovery
- DB Persistence: SQLite (default), can be used with MySql, PgSql
- Apps:
  - [DEMO](https://django-material-dash2.onrender.com/dynamic-dt/product/) **Dynamic DataTables** - generate server-side datatables without coding
  - [DEMO](https://django-material-dash2.onrender.com/api/product/) **Dynamic APIs** - Expose secure APIs without coding  
  - [DEMO](https://django-material-dash2.onrender.com/charts/) **Charts** - powered by ApexCharts 
- [Django CLI Package](https://app-generator.dev/docs/developer-tools/django-cli/index.html)
    - `Commit/rollback Git Changes`
    - `Backup & restore DB`
    - `Interact with Django Core`
    - `Manage Environment`
    - `Manage Dependencies`  
- [Deployment](https://app-generator.dev/docs/deployment.html)
  - Docker/Docker Compose Scripts 
  - CI/CD for [Render](https://app-generator.dev/docs/deployment/render/index.html)
- [Vite](https://app-generator.dev/docs/technologies/vite/index.html) for assets management 

![Django Material Dashboard - Open-Source Django Starter](https://github.com/user-attachments/assets/dba1a100-3309-400c-99bc-6ba707697509)

<br />

## Table of Contents

* [Demo](#demo)
* [Quick Start](#quick-start)
* [Documentation](#documentation)
* [File Structure](#file-structure)
* [Browser Support](#browser-support)
* [Resources](#resources)
* [Reporting Issues](#reporting-issues)
* [Technical Support or Questions](#technical-support-or-questions)
* [Licensing](#licensing)
* [Useful Links](#useful-links)

<br />

## Demo

> To authenticate use the default credentials or create a new user on the **registration page**.

- **Material Dashboard Django** [Login Page](https://www.creative-tim.com/live/material-dashboard-django)

<br />

## Quick start

> 👉 Download the code  

```bash
$ git clone https://github.com/creativetimofficial/material-dashboard-django.git
$ cd material-dashboard-django
```

<br />

> 👉 Install modules via `VENV`  

```bash
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

<br />

> 👉 Set Up Database

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

<br />

> 👉 Create the Superuser

```bash
$ python manage.py createsuperuser
```

<br />

> 👉 Start the app

```bash
$ python manage.py runserver
```

At this point, the app runs at `http://127.0.0.1:8000/`. 

<br />

## Documentation

The documentation for the **Soft UI Dashboard Django** is hosted at our [website](https://app-generator.dev/docs/products/django/soft-ui-dashboard/index.html).

<br />

## Codebase structure

The project is coded using a simple and intuitive structure presented below:

```bash
< PROJECT ROOT >
   |
   |-- config/                            
   |    |-- settings.py                  # Project Configuration  
   |    |-- urls.py                      # Project Routing
   |
   |-- apps/
   |    |-- charts                        
   |    |-- dyn_api                      # APP Routing
   |    |-- dyn_dt                       # APP Models 
   |    |-- pages                        # Tests  
   |     
   |-- requirements.txt                  # Project Dependencies
   |
   |-- env.sample                        # ENV Configuration (default values)
   |-- manage.py                         # Start the app - Django default start script
   |
   |-- ************************************************************************
```

<br />

## Deploy on [Render](https://render.com/)

- Create a Blueprint instance
  - Go to https://dashboard.render.com/blueprints this link.
- Click `New Blueprint Instance` button.
- Connect your `repo` which you want to deploy.
- Fill the `Service Group Name` and click on `Update Existing Resources` button.
- After that your deployment will start automatically.

At this point, the product should be LIVE.

<br />

## Reporting Issues

We use GitHub Issues as the official bug tracker for the **Material Dashboard Django**. Here are some advices for our users that want to report an issue:

1. Make sure that you are using the latest version of the **Material Dashboard Django**. Check the CHANGELOG from your dashboard on our [website](https://www.creative-tim.com/).
2. Providing us reproducible steps for the issue will shorten the time it takes for it to be fixed.
3. Some issues may be browser-specific, so specifying in what browser you encountered the issue might help.

<br />

## Support

Being a product that is actively supported and improved, feel free to contact us using these funnels: 

- **Creative-Tim** [Discord](https://discord.gg/haJ7ErsNY3) Server - for general product assistance and UI/UX
- **App Generator** [Discord](https://discord.gg/fZC6hup) Server - for **Django specific questions** and assistance. 

<br />

## Licensing

- Copyright 2019 - present [Creative Tim](https://www.creative-tim.com/)
- Licensed under [Creative Tim EULA](https://www.creative-tim.com/license)

<br />

## Useful Links

- [More products](https://www.creative-tim.com/bootstrap-themes) from Creative Tim
- [Tutorials](https://www.youtube.com/channel/UCVyTG4sCw-rOvB9oHkzZD1w)
- [Freebies](https://www.creative-tim.com/bootstrap-themes/free) from Creative Tim
- [Affiliate Program](https://www.creative-tim.com/affiliates/new) (earn money)

<br />

## Social Media

- Twitter: <https://twitter.com/CreativeTim>
- Facebook: <https://www.facebook.com/CreativeTim>
- Dribbble: <https://dribbble.com/creativetim>
- Instagram: <https://www.instagram.com/CreativeTimOfficial>

<br />

---
[Material Dashboard Django](https://www.creative-tim.com/product/material-dashboard-django) - Provided by [Creative Tim](https://www.creative-tim.com/) and [App-Generator](https://app-generator.dev/).
