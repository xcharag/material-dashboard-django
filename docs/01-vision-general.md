# 01 · Visión General

## Propósito del sistema

**CereDB** es un sistema de gestión clínica para profesionales de salud mental
(psicólogos y psiquiatras) orientado al contexto boliviano. Su objetivo es
centralizar en una sola plataforma todo lo que ocurre alrededor de la atención de
un paciente:

- Registro y administración de **pacientes** y **profesionales**.
- Agendamiento de **consultas** con calendario y control de disponibilidad por
  consultorio.
- **Notas clínicas** y **archivos adjuntos** por consulta (exámenes, informes).
- **Gestión financiera**: cobros esperados y pagos parciales/totales.
- **Reportes clínicos con IA**: un asistente que responde preguntas sobre el
  expediente de un paciente usando *Retrieval-Augmented Generation* (RAG).
- **Monitoreo EEG y detección de emociones** mediante una diadema Neurosky y una
  aplicación de escritorio dedicada, con estadísticas visibles en la web.

## Los dos componentes

El proyecto no es una sola aplicación, sino **dos programas independientes que
comparten la misma base de datos**:

| Componente | Tecnología | Rol |
|---|---|---|
| **Aplicación web** | Django 4.2 + Bootstrap 5 (Material Dashboard) | Interfaz principal para el profesional. CRUD clínico, finanzas, IA y visualización de estadísticas EEG. |
| **Aplicación de escritorio** | Python + pywebview + TensorFlow | Se conecta a la diadema Neurosky por Bluetooth, procesa la señal EEG, clasifica emociones con una CNN y escribe las sesiones en la base de datos. |

Ambos escriben y leen la misma base de datos PostgreSQL (`ceredb`). Así, una sesión
grabada en la aplicación de escritorio aparece automáticamente en la sección de
**Estadísticas EEG** de la web sin ninguna sincronización manual.

## ¿Por qué dos aplicaciones separadas?

La captura de EEG requiere:

- **Acceso al hardware local** (puerto serie Bluetooth / COM), imposible desde un
  navegador web por razones de seguridad.
- **Cómputo local** con TensorFlow para ejecutar la red neuronal en tiempo real.

Por eso el monitoreo vive en una aplicación de escritorio nativa, mientras que la
gestión clínica y la visualización viven en la web, accesible desde cualquier
dispositivo. La base de datos compartida es el punto de unión entre ambos mundos.

## Público objetivo y contexto

- **Idioma:** español (locale `es-bo`, zona horaria `America/La_Paz`).
- **Usuarios:** profesionales de salud mental y personal de secretaría.
- **Moneda por defecto:** boliviano (`BOB`).

## Alcance de esta documentación

Cada documento de esta carpeta explica un subsistema y, cuando corresponde, el
concepto técnico de fondo (qué es una CNN, qué es RAG, cómo funciona el protocolo
ThinkGear, etc.), de modo que sirva tanto como referencia de implementación como
material de apoyo para responder preguntas técnicas durante la defensa.

Continúa en → [02 · Arquitectura Global](02-arquitectura.md).
