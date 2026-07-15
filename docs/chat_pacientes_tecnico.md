# Funcionamiento Técnico del Chat de Análisis de Pacientes

## Visión General

El chat de análisis de pacientes es un sistema de **RAG (Retrieval-Augmented Generation)** implementado sobre la API de OpenAI. Su función es permitir al profesional hacer preguntas en lenguaje natural sobre el expediente clínico de un paciente específico, obteniendo respuestas fundamentadas en los datos reales del sistema.

El flujo completo involucra tres capas:
1. **Base de datos local** (SQLite/PostgreSQL con Django ORM)
2. **OpenAI Files API + Vector Stores** (índice semántico externo)
3. **OpenAI Responses API con Conversations** (historial de conversación gestionado por OpenAI)

---

## Modelos de Datos Involucrados

### `PatientAIThread` (`apps/pages/models.py:249`)

Tabla pivot que representa **una sesión de conversación** entre un profesional y el expediente de un paciente. Hay exactamente un `PatientAIThread` por par `(professional, patient)` (restricción `unique_together`).

| Campo | Tipo | Propósito |
|---|---|---|
| `professional` | FK | Profesional dueño del thread |
| `patient` | FK | Paciente al que pertenece el expediente |
| `model` | CharField | Modelo LLM a usar (por defecto `gpt-5`) |
| `context` | TextField | Snapshot plano de notas/consultas en texto |
| `openai_conversation_id` | CharField | ID de la conversación en OpenAI Responses API |
| `openai_vector_store_id` | CharField | ID del Vector Store en OpenAI (índice RAG) |
| `context_consult_count` | IntegerField | Contador de consultas al momento del último build |
| `context_note_count` | IntegerField | Contador de notas al momento del último build |
| `context_attachment_count` | IntegerField | Contador de adjuntos al momento del último build |
| `context_last_consultation` | FK nullable | Última consulta incluida en el contexto |

### `PatientAIMessage` (`apps/pages/models.py:275`)

Espejo local de cada turno de la conversación. OpenAI mantiene el historial en su lado (via `openai_conversation_id`); este modelo duplica el historial para renderizado en la UI y para la exportación a PDF.

| Campo | Tipo | Propósito |
|---|---|---|
| `thread` | FK | Thread al que pertenece el mensaje |
| `role` | CharField | `user` / `assistant` / `system` |
| `content` | TextField | Texto del mensaje |
| `is_summary` | BooleanField | Marca si es el resumen inicial estructurado |

### `ConsultationAttachment` (`apps/pages/models.py:149`)

Archivos adjuntos a consultas (PDFs, imágenes, informes). El campo clave para la IA:

| Campo | Tipo | Propósito |
|---|---|---|
| `openai_file_id` | CharField nullable | ID retornado por OpenAI Files API al subir el archivo |

---

## Pipeline de Inicialización del Chat

### Paso 1 — Disparo (`POST /report/sessions/`)

Cuando el profesional selecciona un paciente y hace submit, `report_sessions` (`views.py:1830`) ejecuta:

**1.1 Get-or-create del thread**
```python
thread, created = PatientAIThread.objects.get_or_create(
    professional=thread_prof,
    patient=selected_patient,
)
```

**1.2 Detección de cambios (dirty-check)**

Antes de reconstruir el contexto, el sistema compara contadores para evitar trabajo innecesario:
```python
unchanged = (
    thread.context_consult_count == cur_consult_count and
    thread.context_note_count    == cur_note_count    and
    thread.context_attachment_count == cur_att_count  and
    thread.context_last_consultation_id == cur_last_consult.id
)
```
Si no hay cambios y no se forzó (`force=1`), se omite la reconstrucción del contexto y del Vector Store.

### Paso 2 — Construcción del Contexto (`_build_patient_context`, `views.py:1637`)

Se serializa el expediente completo a texto plano estructurado:

```
Paciente: Juan Pérez
Total de consultas: 12
- Consulta: 2025-03-10 10:00, estado=Terminada, duración=60 min
  Notas:
   • Evaluación inicial: Paciente refiere ansiedad generalizada...
  Adjuntos:
   • Exámenes - escala_hamilton.pdf
- Consulta: 2025-04-07 11:30, ...
```

Este texto cumple dos funciones:
- Se persiste en `thread.context` como caché local.
- Se sube a OpenAI como archivo `.txt` indexable.

### Paso 3 — Construcción del Vector Store (`_ensure_patient_vector_store`, `views.py:1701`)

El Vector Store es el **índice semántico externo** que permite al modelo recuperar fragmentos relevantes por similitud en lugar de recibir el expediente completo en cada turno.

**3.1** Si ya existe un Vector Store anterior, se elimina para evitar costos huérfanos en OpenAI:
```python
client.vector_stores.delete(thread.openai_vector_store_id)
```

**3.2** Se sube el texto de notas clínicas como archivo indexable:
```python
notes_file = client.files.create(
    file=(notes_filename, io.BytesIO(context_text.encode('utf-8')), 'text/plain'),
    purpose='assistants',
)
```

**3.3** Se suben los adjuntos binarios (PDFs, etc.) vía `_ensure_openai_file` (`views.py:1671`). Esta función es idempotente: si `attachment.openai_file_id` ya existe, reutiliza el ID sin resubir el archivo.

**3.4** Se crea el Vector Store con todos los file IDs y se indexa de forma síncrona:
```python
vs = client.vector_stores.create(
    name=f"paciente_{patient.id}_{patient.last_name}",
    expires_after={"anchor": "last_active_at", "days": 90},
)
client.vector_stores.file_batches.create_and_poll(
    vector_store_id=vs.id,
    file_ids=all_file_ids,  # [notes_file.id] + attachment_file_ids
)
```
El `create_and_poll` bloquea hasta que la indexación termine — el Vector Store queda listo para búsquedas antes de continuar.

### Paso 4 — Creación de la Conversación y Resumen Inicial

**4.1** Se crea una nueva conversación (historial server-side):
```python
conv = client.conversations.create(
    items=[{"role": "user", "content": [{"type": "input_text",
        "text": "Eres un asistente clínico para profesionales de salud mental..."}]}]
)
thread.openai_conversation_id = conv.id
```

**4.2** Se genera el resumen estructurado inicial con `file_search` activado:
```python
resp = client.responses.create(
    model=thread.model or 'gpt-5',
    input=[{"role": "user", "content": "Genera el resumen clínico completo..."}],
    conversation=conv.id,
    tools=[{"type": "file_search", "vector_store_ids": [vs_id]}],
)
```

El tool `file_search` hace que el modelo consulte el Vector Store para recuperar los fragmentos más relevantes del expediente antes de generar la respuesta. El historial queda guardado en OpenAI bajo `conv.id`.

**4.3** La respuesta se persiste localmente como `PatientAIMessage(is_summary=True)`.

---

## Pipeline del Chat (Turnos Subsecuentes)

### Endpoint `POST /report/sessions/chat/` (`report_sessions_chat`, `views.py:2022`)

Cada mensaje del profesional pasa por este endpoint AJAX:

**1.** Se persiste el mensaje del usuario localmente:
```python
PatientAIMessage.objects.create(thread=thread, role='user', content=question)
```

**2.** Se llama a la Responses API **continuando la conversación existente**:
```python
resp = client.responses.create(
    model=thread.model or 'gpt-5',
    input=[{"role": "user", "content": question}],
    conversation=thread.openai_conversation_id,  # reutiliza el historial
    tools=[{"type": "file_search", "vector_store_ids": [vs_id]}],
)
```

Al pasar `conversation=thread.openai_conversation_id`, OpenAI reconstruye automáticamente el historial de la sesión en su lado — no se reenvía el contexto completo en cada turno. El modelo tiene acceso al Vector Store para recuperar información del expediente cuando la necesita.

**3.** Se implementa reintentos exponenciales para el error `conversation_locked` (OpenAI procesa un turno a la vez):
```python
for attempt in range(4):
    try:
        resp = client.responses.create(...)
        break
    except Exception as e:
        if 'conversation_locked' in str(e):
            time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
            continue
```

**4.** La respuesta se persiste localmente y se retorna como JSON:
```python
PatientAIMessage.objects.create(thread=thread, role='assistant', content=answer)
return JsonResponse({'ok': True, 'answer': answer})
```

---

## Exportación a PDF (`report_sessions_pdf`, `views.py:1956`)

1. Se recupera el último `PatientAIMessage(is_summary=True)` del thread.
2. El contenido Markdown se convierte a HTML con `markdown.markdown()`.
3. Se renderiza en la plantilla `report_sessions_pdf.html`.
4. `xhtml2pdf.pisa.CreatePDF()` genera el binario PDF.
5. Se retorna como `HttpResponse` con `Content-Disposition: attachment`.

---

## Diagrama de Flujo

```
[Profesional selecciona paciente]
         │
         ▼
[GET /report/sessions/?patient=N]
         │
         ▼
[Profesional hace submit]
         │
         ▼
[POST /report/sessions/]
         │
    ┌────┴────────────────────────────────┐
    │  ¿Contexto cambió? (dirty-check)    │
    │  (consult_count, note_count,        │
    │   att_count, last_consultation)     │
    └────┬──────────────┬─────────────────┘
    SÍ cambió          NO cambió
         │                  │
         ▼                  ▼
[_build_patient_context]  [Muestra resumen anterior]
[Serializa consultas,
 notas y adjuntos a texto]
         │
         ▼
[_ensure_patient_vector_store]
  • Elimina Vector Store anterior
  • Sube notas .txt a Files API
  • Sube adjuntos binarios (idempotente)
  • Crea Vector Store + indexa (crea_and_poll)
         │
         ▼
[client.conversations.create]
  → openai_conversation_id guardado en DB
         │
         ▼
[client.responses.create + file_search]
  → Resumen estructurado (A/B/C)
  → PatientAIMessage(is_summary=True) guardado
         │
         ▼
[Interfaz renderizada con resumen + chat]
         │
         ▼ (turnos de chat)
[POST /report/sessions/chat/]
  → client.responses.create(conversation=existing_id)
  → RAG via file_search sobre Vector Store
  → PatientAIMessage(role='user'/'assistant') guardados
         │
         ▼ (opcional)
[GET /report/sessions/pdf/]
  → Último is_summary → Markdown → HTML → PDF
```

---

## Consideraciones Técnicas Relevantes

### Idempotencia de archivos adjuntos
`_ensure_openai_file` verifica `attachment.openai_file_id` antes de subir. Si ya existe, retorna el ID sin llamar a la API. Esto evita duplicados y reduce costos, pero significa que **si un adjunto se modifica localmente, el archivo en OpenAI queda desactualizado** hasta que se use el endpoint de re-subida (`POST /report/sessions/reupload/`).

### Historial de conversación: local vs. remoto
El historial vive en **dos lugares simultáneamente**:
- **OpenAI (fuente de verdad para inferencia)**: gestionado bajo `openai_conversation_id`. El modelo lo reconstruye automáticamente en cada turno.
- **DB local (fuente de verdad para UI y exportación)**: tabla `PatientAIMessage`. Permite renderizar el chat sin llamadas a OpenAI y generar el PDF.

### Modelo LLM
El modelo por defecto al momento del código es `gpt-5`. Está almacenado por thread en `PatientAIThread.model`, lo que permite migrarlo por paciente sin afectar conversaciones activas.

### Seguridad de acceso
Todas las vistas validan que el profesional autenticado sea el dueño del thread (`thread.professional_id == prof.id`). Los secretarios están completamente excluidos del módulo de IA via `_is_secretary()`.

### Costo de almacenamiento en OpenAI
Los Vector Stores tienen expiración de 90 días con `anchor: last_active_at`. Cada vez que se regenera el contexto se elimina el anterior para evitar acumulación de stores huérfanos.
