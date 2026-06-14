# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 4.2 clinical management system (thesis project) with AI-powered session reporting. Built on Material Dashboard 5 (Bootstrap 5), targeting Spanish-speaking healthcare professionals in Bolivia. Features multi-professional support, patient/consultation management, calendar scheduling, financial tracking, and OpenAI integration for intelligent clinical summaries.

## Common Commands

```bash
# Development server
python manage.py runserver

# Database
python manage.py migrate
python manage.py makemigrations

# Static files (production)
python manage.py collectstatic --no-input

# Admin user
python manage.py createsuperuser

# Django shell
python manage.py shell

# Docker (with Nginx reverse proxy on port 5085)
docker-compose up --build
```

**No test suite is configured.** There is no pytest/unittest setup in this project.

## Environment Setup

Copy `env.sample` to `.env` and fill in:

```
DEBUG=True
SECRET_KEY=<generate with get_random_secret_key()>
OPENAI_API_KEY=sk-...
# Database defaults to SQLite if DB_ENGINE is not set
DB_ENGINE=postgresql
DB_HOST=...
DB_NAME=...
DB_USERNAME=...
DB_PASS=...
DB_PORT=5432
# Email for password reset
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

## Architecture

### Django Apps

| App | Purpose |
|-----|---------|
| `apps.pages` | Core: patients, professionals, consultations, sessions, AI reports, auth |
| `apps.finance` | Payment requests and individual payment transactions |
| `apps.charts` | ApexCharts data visualization (no models) |
| `apps.dyn_dt` | Dynamic DataTables (filters, pagination) |
| `apps.dyn_api` | Dynamic REST API generation |

Config lives in `config/` (settings.py, urls.py, wsgi.py).

### Key Model Relationships

```
Professional --< Patient (optional assignment)
Professional >--< Specialty (ManyToMany)
Patient --< Consultation >-- Professional
Consultation --< ConsultationNote
Consultation --< ConsultationAttachment (stores openai_file_id)
Professional >-- PatientAIThread >-- PatientAIMessage
Patient >-- PatientAIThread
Consultation >-- PaymentRequest --< Payment
```

**PatientAIThread** is central to the AI feature: it holds one `openai_conversation_id` (Responses API) and one `openai_vector_store_id` (RAG) per professional–patient pair.

### AI Integration (OpenAI)

The `/report/sessions/` flow:
1. Professional selects a patient → system builds clinical context from consultations, notes, and attachments.
2. A `PatientAIThread` is created or reused (stores `openai_conversation_id` + `openai_vector_store_id`).
3. Attachments are uploaded via the Files API; their `openai_file_id` is persisted on `ConsultationAttachment`.
4. Chat uses the OpenAI Responses API with server-side conversation history; messages are also persisted locally in `PatientAIMessage`.
5. PDF export available via xhtml2pdf.

**Model default:** `gpt-4o-mini`. Both `openai` (>=1.47.0) and `anthropic` (0.34.2) SDKs are installed, but only OpenAI is active in views.

To reset AI state for a patient:
```python
from apps.pages.models import PatientAIThread, PatientAIMessage
PatientAIMessage.objects.filter(thread__patient_id=<id>).delete()
PatientAIThread.objects.filter(patient_id=<id>).update(openai_conversation_id='', openai_vector_store_id='', context='')
```

### URL Structure

Main namespaces in `apps/pages/urls.py`:
- `/` — Dashboard
- `/patients/`, `/professionals/`, `/consult/` — CRUD management
- `/start-session/<id>/`, `/end-session/<id>/` — Session workspace
- `/mis-pacientes/` — Professional's own patient list and history
- `/report/sessions/` — AI report generator + chat + PDF
- `/config/consultorios/calendario/` — Availability calendar
- `/profile/` — User profile (5 tabs: info, schedule, contacts, media, security)
- `/api/available-slots/`, `/api/calendar/events/` — JSON APIs

### Frontend

- Bootstrap 5 via Material Dashboard (Creative Tim) + Jazzmin for Django admin
- Custom JS/CSS in `static/`: `custom-combo.js`, `page-loader.js`, `toasts.js`
- `vite.config.js` and `package.json` present but assets are mostly pre-built static files
- Templates in `templates/` with `apps/pages/templates/` for app-specific views
- Language: Spanish (locale `es-bo`, timezone `America/La_Paz`)

### Management Commands

- `python manage.py clear_consultations` — Clear consultation data
- `python manage.py seed_availability` — Populate weekly availability schedules

### Deployment

- `build.sh` — Runs pip install, collectstatic, migrate (used by Render)
- `render.yaml` — Render.com config (gunicorn, DEBUG=False, WEB_CONCURRENCY=4)
- `docker-compose.yml` — Django + Nginx on port 5085
- `gunicorn-cfg.py` — Binds 0.0.0.0:5005, 1 worker
