# Documentación Técnica — Proyecto CereDB

Documentación técnica completa del sistema de gestión clínica **CereDB** y su
aplicación de escritorio de monitoreo EEG. Este material está pensado como
referencia rápida durante la defensa de tesis: cada documento explica un
componente del sistema junto con los conceptos técnicos que lo sustentan.

## ¿Qué es el proyecto?

El proyecto consta de **dos aplicaciones** que comparten una única base de datos
PostgreSQL:

1. **Aplicación web (Django)** — sistema de gestión clínica para profesionales de
   salud mental: pacientes, consultas, calendario, finanzas, reportes con IA y
   estadísticas EEG.
2. **Aplicación de escritorio (Python + pywebview)** — captura señales EEG del
   dispositivo Neurosky Mindwave Mobile 2, detecta emociones con una red neuronal
   convolucional (CNN) y guarda las sesiones en la misma base de datos.

## Índice

### Visión general
- [01 · Visión General](01-vision-general.md) — qué resuelve el sistema y su alcance.
- [02 · Arquitectura Global](02-arquitectura.md) — componentes, stack tecnológico y cómo se comunican.
- [03 · Modelo de Datos](03-modelo-de-datos.md) — todas las tablas, relaciones y diagrama entidad-relación.

### Aplicación web (Django)
- [04 · Aplicación Web](04-aplicacion-web.md) — apps de Django, vistas, rutas, roles y autenticación.
- [05 · Módulo de Finanzas](05-modulo-finanzas.md) — cobros, pagos y estados de cuenta.
- [06 · IA de Análisis de Pacientes](06-ia-analisis-pacientes.md) — chat clínico con RAG sobre OpenAI.
- [Detalle técnico del chat clínico](chat_pacientes_tecnico.md) — pipeline completo del RAG.

### Aplicación de escritorio (EEG)
- [07 · Aplicación de Escritorio EEG](07-app-escritorio-eeg.md) — arquitectura pywebview y flujo de datos.
- [08 · Neurosky y el Protocolo ThinkGear](08-neurosky-thinkgear.md) — cómo se lee la señal del dispositivo.
- [09 · Procesamiento de la Señal](09-procesamiento-senal.md) — del EEG crudo al vector de 2548 características.
- [10 · Modelo CNN de Emociones](10-modelo-cnn-emociones.md) — arquitectura, entrenamiento y precisión.
- [11 · Integración de Datos EEG ↔ Web](11-integracion-datos.md) — sincronización y estadísticas.

### Operación
- [12 · Despliegue](12-despliegue.md) — cómo se ejecuta y publica cada aplicación.
- [13 · Glosario Técnico](13-glosario.md) — definiciones de todos los términos técnicos usados.

## Cómo publicar esta documentación

Los archivos son Markdown estándar; se pueden leer directamente en GitHub. Para
tener una **página web navegable** (buscador, menú lateral) se incluye un archivo
`mkdocs.yml` en la raíz del repositorio:

```bash
pip install mkdocs mkdocs-material
mkdocs serve      # vista previa local en http://127.0.0.1:8000
mkdocs gh-deploy  # publica en GitHub Pages
```

Consulta [12 · Despliegue](12-despliegue.md) para más detalles de hosting.
