# 11 · Integración de Datos EEG ↔ Web

Este documento explica cómo una sesión grabada en la aplicación de escritorio
aparece, sin pasos manuales, en las estadísticas de la aplicación web. La clave es la
**base de datos PostgreSQL compartida**.

## Ciclo de vida de una sesión

```
[App escritorio]                         [Base de datos]            [App web]
      │                                        │                        │
  start_session ──► INSERT pages_eegsession ──►│                        │
      │            (started_at, patient_id)    │                        │
      │                                        │                        │
  (por cada lectura, ~5/s mientras hay sesión) │                        │
  add_reading ────► INSERT pages_eegreading ──►│                        │
      │            (attention, meditation,     │                        │
      │             bandas, emoción)           │                        │
      │                                        │                        │
  stop_session ──► UPDATE pages_eegsession ───►│                        │
      │            (ended_at,                  │                        │
      │             dominant_emotion)          │                        │
      │                                        │  GET /report/eeg/ ────►│
      │                                        │◄──── SELECT ...        │
      │                                        │   (estadísticas)       │
```

## Lado escritorio: `SessionManager`

`backend/session_manager.py` controla la grabación:

- **`start(patient_id, patient_name, operator)`** — inserta una fila en
  `pages_eegsession` con `started_at = ahora (UTC)` y guarda el `session_id`
  devuelto. Marca la sesión como activa.
- **`add_reading(reading)`** — llamado desde el bucle de *polling* con cada paquete.
  Añade la lectura a un buffer en memoria, actualiza un contador de emociones
  (`Counter`) e inserta la fila en `pages_eegreading`. La escritura a BD ocurre en un
  hilo para no bloquear la UI; si falla, la lectura se pierde sin cortar la sesión.
- **`stop()`** — calcula la **emoción dominante** (la más frecuente del `Counter`),
  hace `UPDATE` de `ended_at` y `dominant_emotion`, y guarda además un **respaldo
  local** en `data/sessions/<fecha>_<paciente>.json`.

### Concepto: emoción dominante

Durante la sesión se registran cientos de lecturas, cada una con su etiqueta de
emoción. Al cerrar, se toma la etiqueta **más frecuente** como resumen de toda la
sesión (`emotion_counter.most_common(1)`). Ese valor es el que se muestra como
emoción de la sesión en la web.

## Lado escritorio: `db_client`

`backend/db_client.py` habla SQL directo (`psycopg2`) contra las tablas que Django
generó. No usa el ORM. Funciones clave:

| Función | SQL |
|---|---|
| `create_session` | `INSERT INTO pages_eegsession ... RETURNING id` |
| `insert_reading` | `INSERT INTO pages_eegreading (...)` |
| `close_session` | `UPDATE pages_eegsession SET ended_at, dominant_emotion` |
| `get_patients` | `SELECT ... FROM pages_patient` (para el selector de paciente) |
| `get_sessions` | `SELECT` con `JOIN` y `COUNT` de lecturas (historial) |

> **Importante:** los nombres de tabla (`pages_eegsession`, `pages_eegreading`,
> `pages_patient`) son los que Django crea automáticamente a partir de
> `app_label + modelo`. La app de escritorio depende de esa convención.

## Lado web: estadísticas EEG

La vista `eeg_stats` (`/report/eeg/`) lee los mismos datos con el ORM de Django y los
presenta con **ApexCharts**:

- Tarjetas resumen: total de sesiones, pacientes con datos EEG, emoción dominante
  global.
- **Distribución de emociones** (dona).
- **Potencia de bandas por sesión** (líneas, promedio por sesión).
- **Atención y Meditación por sesión** (área).
- **Historial de sesiones** (tabla con fecha, paciente, operador, duración, emoción
  dominante y nº de lecturas).

Los promedios por sesión se calculan con agregaciones del ORM
(`EEGReading.objects.filter(session=s).aggregate(Avg(...))`).

## Datos que fluyen por lectura

| Campo web (`EEGReading`) | Origen en escritorio |
|---|---|
| `attention`, `meditation` | eSense de Neurosky (0–100). |
| `delta`, `theta`, `alpha`, `beta`, `gamma` | Potencias de banda (alpha/gamma combinan sus sub-bandas). |
| `emotion_label` | Salida de la CNN (POSITIVE/NEUTRAL/NEGATIVE). |
| `emotion_confidence` | Probabilidad softmax del modelo (0–1). |

## Respaldo local

Además de la base de datos, cada sesión se guarda como JSON en
`data/sessions/`. Sirve como copia de seguridad si la conexión a la base de datos
falla durante el cierre.

## Instalador

La web ofrece la descarga del instalador de la app de escritorio en
`/report/eeg/download-installer/` (`EEGMonitor_Setup.zip`), de modo que el
profesional pueda instalarla desde la propia plataforma.

Continúa en → [12 · Despliegue](12-despliegue.md).
