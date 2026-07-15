# 03 · Modelo de Datos

Todos los modelos están definidos con el **ORM de Django** en
`apps/pages/models.py` (núcleo clínico + IA + EEG) y `apps/finance/models.py`
(finanzas). Django genera los nombres de tabla con el prefijo de la app:
`pages_patient`, `pages_consultation`, `finance_payment`, etc.

## Diagrama entidad-relación (resumen)

```
                 ┌───────────────┐
                 │ User (Django) │
                 └──────┬────────┘
                        │ 1:1
                 ┌──────▼────────┐        M:N       ┌────────────┐
                 │ Professional  ├─────────────────►│ Specialty  │
                 └──────┬────────┘                  └────────────┘
          1:N ┌─────────┼──────────┬──────────────┬─────────────┐
              ▼         ▼          ▼              ▼             ▼
        ┌─────────┐ ┌────────┐ ┌────────────┐ ┌──────────┐ ┌───────────────────┐
        │ Patient │ │Weekly  │ │Professional│ │Availabil.│ │ ProfessionalContact│
        │         │ │Availab.│ │  Media     │ │Exception │ │                    │
        └────┬────┘ └────────┘ └────────────┘ └──────────┘ └───────────────────┘
             │ 1:N
             ▼
      ┌───────────────┐   1:N   ┌───────────────────┐
      │ Consultation  ├────────►│ ConsultationNote  │
      │               ├────────►│ ConsultationAttach│──► openai_file_id
      └───┬───────┬───┘   1:N   └───────────────────┘
          │       │ 1:1
          │       ▼
          │  ┌──────────────┐  1:N  ┌──────────┐
          │  │PaymentRequest├──────►│ Payment  │
          │  └──────────────┘       └──────────┘
          │
          ▼ (por consultorio)
      ┌──────────────┐
      │ Consultorio  │
      └──────────────┘

   Professional ──1:N──► PatientAIThread ──1:N──► PatientAIMessage
   Patient      ──1:N──► PatientAIThread

   Patient ──1:N──► EEGSession ──1:N──► EEGReading
```

## Núcleo clínico

### `Patient` — Paciente
Datos personales del paciente. Puede tener un `Professional` asignado (opcional) y
un `color` hex para el calendario.

Campos clave: `first_name`, `last_name`, `email`, `phone`, `date_of_birth`,
`address`, `professional` (FK), `color`.

### `Professional` — Profesional
Representa al usuario clínico. Se enlaza 1:1 con el `User` de Django (autenticación).

| Campo | Propósito |
|---|---|
| `user` | Enlace 1:1 con el usuario de login de Django |
| `role` | `psychologist`, `psychiatrist` o `secretary` |
| `specialties` | Relación M:N con `Specialty` |
| Perfil extendido | `profile_picture`, `biography`, `gender`, `nationality`, `identification_type/number`, `license_number`, `education`, `years_experience`, `languages_spoken`, … |

El rol **`secretary`** existe para personal administrativo con acceso restringido
(por ejemplo, excluido del módulo de IA).

### `Consultation` — Consulta / Cita
El evento central de agenda y atención.

| Campo | Propósito |
|---|---|
| `patient`, `professional` | Participantes (FK) |
| `consultorio_fk` | Consultorio físico (FK a `Consultorio`) |
| `date`, `time`, `duration` | Cuándo y por cuánto (minutos, def. 60) |
| `charge` | Monto a cobrar (Decimal) |
| `status` | `pending`, `attended`, `completed`, `no_show`, `cancelled` |

### `ConsultationNote` — Nota clínica
Texto libre asociado a una consulta (`title`, `content`, `created_by`). Una consulta
puede tener varias notas (registro de sesión).

### `ConsultationAttachment` — Adjunto
Archivo subido a una consulta (`file`, `file_type` ∈ notas/exámenes/resultados/
documentos). El campo **`openai_file_id`** guarda el identificador del archivo una
vez subido a la Files API de OpenAI, para que la IA pueda leerlo (ver doc 06).

### `Consultorio` — Consultorio
Espacio físico donde se atiende (`name`, `address`, `is_active`).

### `Specialty` — Especialidad
Catálogo de especialidades (`name` único). Relación M:N con `Professional`.

## Disponibilidad y agenda

### `WeeklyAvailability` — Disponibilidad semanal
Horario recurrente por día de la semana y profesional (`weekday`, `start_time`,
`end_time`, `is_closed`). Restricción única por `(professional, weekday)`.

### `AvailabilityException` — Excepción de disponibilidad
Ajuste puntual para una fecha concreta (feriado, jornada especial). Único por
`(professional, date)`.

Estas dos tablas alimentan el cálculo de horarios libres del calendario
(`apps/pages/utils/availability.py`).

## Perfil del profesional

- `ProfessionalContact` — contactos (website, teléfono, correo, redes).
- `ProfessionalMedia` — galería de imágenes del perfil.

## Módulo de IA

### `PatientAIThread`
Una conversación de IA por par `(professional, patient)` (único). Guarda los IDs de
OpenAI (`openai_conversation_id`, `openai_vector_store_id`) y contadores para saber
si el contexto cambió. Detalle completo en
[chat_pacientes_tecnico.md](chat_pacientes_tecnico.md).

### `PatientAIMessage`
Espejo local de cada turno de la conversación (`role`, `content`, `is_summary`) para
renderizar el chat y exportar a PDF.

## Módulo EEG

Estas tablas son **escritas por la aplicación de escritorio** y **leídas por la
web** para las estadísticas.

### `EEGSession` — Sesión EEG
Una grabación completa con una diadema.

| Campo | Propósito |
|---|---|
| `patient` | Paciente monitoreado (FK) |
| `operator_name` | Quién operó el equipo |
| `started_at`, `ended_at` | Inicio y fin de la grabación |
| `dominant_emotion` | Emoción más frecuente de la sesión (`POSITIVE`/`NEUTRAL`/`NEGATIVE`) |
| `duration_seconds` / `duration_display` | Propiedades calculadas (p. ej. "4 min 16 s") |

### `EEGReading` — Lectura EEG
Una muestra puntual dentro de una sesión (se guardan muchas por segundo de
actividad).

| Campo | Propósito |
|---|---|
| `session` | Sesión a la que pertenece (FK) |
| `timestamp` | Momento de la lectura |
| `attention`, `meditation` | Índices eSense de Neurosky (0–100) |
| `delta`…`gamma` | Potencias de banda |
| `emotion_label`, `emotion_confidence` | Salida del modelo CNN |

## Finanzas

### `PaymentRequest` — Solicitud de cobro
Uno por consulta (1:1). Define el `expected_amount` y calcula propiedades derivadas:
`amount_paid`, `balance`, y `status` (`pending`/`partial`/`paid`).

### `Payment` — Pago
Cada transacción concreta contra una solicitud (`amount`, `method` ∈ efectivo/
tarjeta/QR, `reference`, `paid_at`). Un `PaymentRequest` puede recibir varios
`Payment` (pagos parciales). Ver [05 · Módulo de Finanzas](05-modulo-finanzas.md).

Continúa en → [04 · Aplicación Web](04-aplicacion-web.md).
