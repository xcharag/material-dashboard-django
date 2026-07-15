# 04 · Aplicación Web (Django)

## Estructura de apps de Django

Un proyecto Django se divide en **apps** (módulos reutilizables). La configuración
global vive en `config/` (`settings.py`, `urls.py`, `wsgi.py`).

| App | Responsabilidad |
|---|---|
| `apps.pages` | Núcleo: pacientes, profesionales, consultas, notas, adjuntos, calendario, sesiones, reportes de IA, autenticación y estadísticas EEG. |
| `apps.finance` | Solicitudes de cobro y pagos. |
| `apps.charts` | Visualización con ApexCharts (sin modelos propios). |
| `apps.dyn_dt` | *Dynamic DataTables*: tablas con filtros y paginación generadas dinámicamente. |
| `apps.dyn_api` | Generación dinámica de una API REST. |
| `admin_material` | Tema Material para el panel de administración. |

## Enrutamiento (URLs)

El enrutador raíz `config/urls.py` incluye las URLs de cada app:

```python
urlpatterns = [
    path('', include('apps.pages.urls')),
    path('', include('apps.dyn_dt.urls')),
    path('', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
    path('finance/', include('apps.finance.urls')),
    path('admin/', admin.site.urls),
    path('', include('admin_material.urls')),
]
```

### Rutas principales (`apps/pages/urls.py`)

| Ruta | Vista | Función |
|---|---|---|
| `/` | `index` | Panel principal (dashboard). |
| `/accounts/login/` | `CustomLoginView` | Inicio de sesión. |
| `/accounts/password-reset/` | vistas de Django | Recuperación de contraseña por correo. |
| `/patients/` | `patients` | Lista y alta de pacientes. |
| `/patients/<id>/edit/`, `/delete/` | `edit_patient`, `delete_patient` | Edición y borrado. |
| `/professionals/` | `professionals` | Gestión de profesionales. |
| `/parameters/` | `parameters` | Catálogos (especialidades). |
| `/consult/` | `consult` | Agenda de consultas. |
| `/consult/list/` | `consult_table` | Tabla de consultas (AJAX). |
| `/start-session/<id>/`, `/end-session/<id>/` | `start_session`, `end_session` | Flujo de atención de una consulta. |
| `/mis-pacientes/` | `my_patients` | Pacientes propios del profesional. |
| `/mis-pacientes/<id>/` | `patient_history` | Historial de un paciente. |
| `/patients/<id>/history-manager/` | `patient_history_manager` | Gestor de historial clínico detallado. |
| `/config/consultorios/` | `config_consultorios` | Configuración de consultorios. |
| `/config/consultorios/calendario/` | `consultorios_calendar` | Calendario de disponibilidad. |
| `/profile/` | `profile` | Perfil del usuario (varias pestañas). |
| `/report/sessions/` | `report_sessions` | Generador de reportes IA + chat. |
| `/report/sessions/chat/` | `report_sessions_chat` | Endpoint AJAX del chat. |
| `/report/sessions/pdf/` | `report_sessions_pdf` | Exportación del reporte a PDF. |
| `/report/eeg/` | `eeg_stats` | Estadísticas EEG. |
| `/report/eeg/download-installer/` | `eeg_download_installer` | Descarga del instalador de escritorio. |

### APIs JSON internas

| Ruta | Uso |
|---|---|
| `/api/available-slots/` | Horarios libres para agendar. |
| `/api/calendar/events/` | Eventos del calendario (FullCalendar). |
| `/consult/update-time/<id>/` | Reprogramar por arrastre en el calendario. |
| `/consult/edit/<id>/`, `/cancel/<id>/`, `/delete/<id>/` | Operaciones sobre consultas. |
| `/patient/<id>/color/` | Cambiar color del paciente en el calendario. |

## Autenticación y roles

- La autenticación usa el sistema estándar de Django (`User`). Cada `Professional`
  se enlaza 1:1 con un `User`.
- El **rol** (`Professional.role`) distingue `psychologist`, `psychiatrist` y
  `secretary`. La secretaría tiene acceso administrativo pero está **excluida del
  módulo de IA** (verificación `_is_secretary()` en las vistas).
- Todas las vistas sensibles usan el decorador `@login_required`. Las vistas de IA
  validan además que el profesional autenticado sea el dueño del thread.

## Frontend

- **Material Dashboard 5** (Bootstrap 5) como base visual.
- Plantillas en `templates/` (layouts base + páginas). Los bloques
  `{% block extrastyle %}` y `{% block extra_js %}` permiten CSS/JS por página.
- **ApexCharts** para los gráficos (estadísticas EEG, finanzas).
- JS/CSS personalizados en `static/` (por ejemplo utilidades de combos, loaders,
  toasts). La librería `apexcharts.min.js` vive en
  `static/assets/js/plugins/`.
- Idioma español; zona horaria `America/La_Paz`.

## Comandos habituales

```bash
python manage.py runserver          # servidor de desarrollo
python manage.py migrate            # aplicar migraciones
python manage.py makemigrations     # generar migraciones al cambiar modelos
python manage.py collectstatic      # recolectar estáticos (producción)
python manage.py createsuperuser    # crear administrador
```

Continúa en → [05 · Módulo de Finanzas](05-modulo-finanzas.md).
