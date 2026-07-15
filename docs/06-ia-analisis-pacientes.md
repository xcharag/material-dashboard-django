# 06 · IA de Análisis de Pacientes

El módulo `/report/sessions/` permite al profesional **conversar en lenguaje natural
sobre el expediente de un paciente** y obtener respuestas fundamentadas en los datos
reales del sistema (consultas, notas, adjuntos).

> Este documento explica los **conceptos**. El **pipeline técnico completo**, con
> números de línea y código, está en
> [chat_pacientes_tecnico.md](chat_pacientes_tecnico.md).

## Concepto: ¿qué es RAG?

**RAG** = *Retrieval-Augmented Generation* (generación aumentada por recuperación).
Es una técnica para que un modelo de lenguaje responda usando **información
específica** que no vio durante su entrenamiento.

En lugar de meter todo el expediente en cada pregunta (costoso y limitado por el
tamaño de contexto), RAG funciona así:

1. **Indexar** los documentos del paciente en un *vector store* (índice semántico).
2. Cuando el profesional pregunta algo, **recuperar** solo los fragmentos más
   relevantes por similitud semántica.
3. **Generar** la respuesta pasando al modelo únicamente esos fragmentos + la
   pregunta.

Así el modelo responde "sobre este paciente" con precisión, sin alucinaciones sobre
datos que no existen y sin reenviar el expediente completo cada vez.

## Concepto: embeddings y vector store

- Un **embedding** es un vector numérico que representa el significado de un texto.
  Textos con significado parecido tienen vectores cercanos.
- Un **vector store** guarda esos vectores y permite buscar "los fragmentos más
  parecidos a esta pregunta" mediante distancia entre vectores.
- OpenAI ofrece Vector Stores gestionados: uno subes archivos, OpenAI los divide en
  fragmentos, calcula embeddings y responde búsquedas con la herramienta
  `file_search`.

## Piezas en OpenAI que usa el sistema

| Servicio de OpenAI | Rol en el sistema |
|---|---|
| **Files API** | Subir el texto de notas y los adjuntos binarios (PDFs). |
| **Vector Stores** | Índice RAG por paciente (notas + adjuntos indexados). |
| **Conversations** | Historial de la conversación gestionado del lado de OpenAI. |
| **Responses API** | Generar respuestas usando `file_search` sobre el vector store. |

## Flujo resumido

```
1. El profesional elige un paciente y hace submit.
2. Se crea/reutiliza un PatientAIThread (uno por profesional-paciente).
3. Dirty-check: si el expediente no cambió, se reutiliza el resumen anterior.
4. Si cambió:
   • Se serializa el expediente a texto plano.
   • Se sube a la Files API y se (re)crea el Vector Store del paciente.
   • Se crea una Conversation y se genera un resumen clínico inicial.
5. Cada pregunta posterior continúa la misma Conversation con file_search
   activado (RAG sobre el Vector Store).
6. Cada turno se guarda también localmente (PatientAIMessage) para la UI y el PDF.
```

## Doble almacenamiento del historial

El historial de la conversación vive en **dos lugares**:

- **OpenAI** (fuente de verdad para la inferencia): bajo `openai_conversation_id`.
  El modelo reconstruye el historial automáticamente en cada turno.
- **Base de datos local** (fuente de verdad para la UI y el PDF): tabla
  `PatientAIMessage`. Permite pintar el chat sin llamar a OpenAI y generar el PDF.

## Optimización: dirty-check

Antes de reconstruir el contexto (operación costosa), el sistema compara contadores
guardados en el thread (`context_consult_count`, `context_note_count`,
`context_attachment_count`, `context_last_consultation`) contra el estado actual. Si
nada cambió y no se forzó (`force=1`), reutiliza el resumen previo. Esto evita
re-subir archivos y re-indexar en cada visita.

## Modelo y seguridad

- **Modelo por defecto:** `gpt-5-mini` con `reasoning={"effort": "low"}`. Se almacena
  por thread (`PatientAIThread.model`), permitiendo migrarlo por paciente. Threads
  antiguos con `gpt-4o-mini`/`gpt-5` se migran automáticamente.
- **Seguridad:** cada vista valida que el profesional autenticado sea dueño del
  thread. La **secretaría queda excluida** del módulo de IA.
- **Costo:** los Vector Stores expiran a los 90 días (`anchor: last_active_at`) y el
  anterior se elimina al regenerar, evitando índices huérfanos.

## Exportación a PDF

El resumen clínico (`PatientAIMessage(is_summary=True)`) se convierte de Markdown a
HTML con `markdown.markdown()` y se renderiza a PDF con `xhtml2pdf`.

Continúa en → [07 · Aplicación de Escritorio EEG](07-app-escritorio-eeg.md).
