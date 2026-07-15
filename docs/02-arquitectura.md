# 02 · Arquitectura Global

## Diagrama de alto nivel

```
        ┌───────────────────────────────────────────────────────────┐
        │                    PROFESIONAL / SECRETARÍA                │
        └───────────────┬───────────────────────────┬───────────────┘
                        │                           │
             (navegador web)              (aplicación de escritorio)
                        │                           │
        ┌───────────────▼───────────────┐   ┌───────▼────────────────────┐
        │   APLICACIÓN WEB (Django 4.2)  │   │  EEG DESKTOP APP (pywebview)│
        │                                │   │                             │
        │  • Gestión clínica (CRUD)      │   │  • Lectura Bluetooth/Serial │
        │  • Calendario / disponibilidad │   │    (Neurosky ThinkGear)     │
        │  • Finanzas                    │   │  • Extracción de features   │
        │  • IA (RAG con OpenAI)         │   │  • CNN de emociones (TF)    │
        │  • Estadísticas EEG            │   │  • Grabación de sesiones    │
        └───────────────┬───────────────┘   └───────────────┬─────────────┘
                        │                                   │
                        │      escrituras / lecturas SQL    │
                        └─────────────────┬─────────────────┘
                                          │
                          ┌───────────────▼───────────────┐
                          │   PostgreSQL  (base "ceredb")  │
                          │   Tablas pages_*, finance_*    │
                          └────────────────────────────────┘
                                          ▲
                          ┌───────────────┴───────────────┐
                          │        OpenAI API (nube)       │
                          │  Files · Vector Stores ·       │
                          │  Conversations · Responses     │
                          └────────────────────────────────┘
```

La **base de datos PostgreSQL compartida** es el eje del sistema. La aplicación web
usa el ORM de Django; la aplicación de escritorio escribe con `psycopg2` (SQL
directo). Los servicios de IA de OpenAI son consumidos únicamente por la web.

## Stack tecnológico

### Aplicación web

| Capa | Tecnología |
|---|---|
| Framework | Django 4.2.9 |
| Base de datos | PostgreSQL (SQLite como fallback local) |
| Frontend | Bootstrap 5 vía Material Dashboard (Creative Tim) |
| Admin | Django Admin con tema Jazzmin + Material |
| Gráficos | ApexCharts |
| IA | SDK `openai` (>=1.47) — Responses API, Vector Stores |
| PDF | `xhtml2pdf` + `Markdown` |
| Archivos estáticos | WhiteNoise |
| Servidor | Gunicorn (producción) |

### Aplicación de escritorio

| Capa | Tecnología |
|---|---|
| Ventana / UI | `pywebview` (HTML/JS renderizado en una webview nativa) |
| Comunicación serie | `pyserial` (protocolo ThinkGear sobre COM Bluetooth) |
| Procesamiento numérico | `numpy`, `scipy` |
| Machine Learning | `tensorflow` / `keras`, `scikit-learn` (scaler) |
| Base de datos | `psycopg2-binary` (conexión directa a PostgreSQL) |
| Empaquetado | PyInstaller (genera un `.exe`) |

## Cómo se comunican los componentes

### Web ↔ Base de datos
Django accede mediante su ORM. Los modelos viven en `apps/pages/models.py` y
`apps/finance/models.py`. Las migraciones definen el esquema de tablas
(`pages_patient`, `pages_consultation`, `pages_eegsession`, etc.).

### Escritorio ↔ Base de datos
`backend/db_client.py` abre conexiones `psycopg2` y ejecuta `INSERT`/`UPDATE`/`SELECT`
directamente sobre las tablas que Django creó. **No** usa el ORM; usa los nombres
de tabla generados por Django (`pages_eegsession`, `pages_eegreading`,
`pages_patient`). Esto lo hace un cliente ligero e independiente de Django.

### Escritorio ↔ Dispositivo Neurosky
`backend/eeg_connector.py` abre el puerto COM Bluetooth a 57600 baudios y decodifica
el flujo binario del protocolo ThinkGear en un hilo en segundo plano. Ver
[08 · Neurosky y el Protocolo ThinkGear](08-neurosky-thinkgear.md).

### Web ↔ OpenAI
Solo el flujo de reportes IA (`/report/sessions/`) llama a OpenAI. Se usan Files
API + Vector Stores (índice RAG) y la Responses API con conversaciones del lado del
servidor. Ver [06 · IA de Análisis de Pacientes](06-ia-analisis-pacientes.md).

### Frontend web (pywebview) ↔ Backend Python
En la aplicación de escritorio, el HTML/JS llama funciones de Python a través del
puente `window.pywebview.api.*`. La clase `Api` (`backend/api.py`) expone métodos
como `get_realtime_data()`, `connect_device()`, `start_session()` que el JavaScript
invoca de forma asíncrona.

## Repositorios

| Repositorio | Contenido |
|---|---|
| `material-dashboard-django` | Aplicación web Django (este repositorio, donde vive esta documentación). |
| `EEGDesktopApp` | Aplicación de escritorio de captura EEG. |

Continúa en → [03 · Modelo de Datos](03-modelo-de-datos.md).
