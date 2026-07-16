# 14 · Seguridad

Este documento describe las medidas de seguridad aplicadas en las dos
aplicaciones del sistema: la web (Django) y la de escritorio (acceso directo a
PostgreSQL con `psycopg2`).

## Aplicación web (Django)

### Autenticación

- Se usa el sistema estándar de Django (`django.contrib.auth`): sesiones del
  lado del servidor, `CustomLoginView` para el inicio de sesión y recuperación
  de contraseña por correo con tokens de un solo uso.
- Cada `Professional` está enlazado 1:1 con un `User`; toda vista sensible
  exige sesión activa mediante el decorador `@login_required`.
- Las sesiones se almacenan en la base de datos (`cached_db`), nunca en el
  cliente; el navegador solo guarda la cookie de sesión.

### Contraseñas

- Django **nunca guarda contraseñas en texto plano**: se almacenan como hash
  con **PBKDF2-SHA256** y sal aleatoria por usuario (comportamiento por
  defecto del framework).
- `AUTH_PASSWORD_VALIDATORS` activa cuatro validadores al crear o cambiar una
  contraseña: similitud con datos del usuario, longitud mínima, lista de
  contraseñas comunes y contraseñas puramente numéricas.

### Autorización y roles

- El rol (`Professional.role`) distingue `psychologist`, `psychiatrist` y
  `secretary`. La secretaría queda **excluida del módulo de IA** mediante la
  verificación `_is_secretary()` en las vistas.
- Las vistas del chat clínico validan que el profesional autenticado sea el
  **dueño del thread** (`PatientAIThread`) antes de mostrar o continuar una
  conversación, de modo que un profesional no puede leer los hilos de otro.

### Protecciones del framework

| Amenaza | Protección |
|---|---|
| **Inyección SQL** | Todas las consultas de la web pasan por el **ORM de Django**, que genera consultas parametrizadas: los valores viajan separados del SQL y nunca se concatenan. |
| **XSS** (inyección de scripts) | El motor de plantillas de Django **escapa automáticamente** todo el contenido variable (`{{ ... }}`) antes de renderizarlo. |
| **CSRF** (peticiones falsificadas) | `CsrfViewMiddleware` exige un token único por sesión en cada formulario POST; los orígenes permitidos se declaran en `CSRF_TRUSTED_ORIGINS`. |
| **Clickjacking** | `XFrameOptionsMiddleware` envía `X-Frame-Options: DENY`, impidiendo embeber la aplicación en iframes de terceros. |
| **Cabeceras de seguridad** | `SecurityMiddleware` añade cabeceras como `X-Content-Type-Options: nosniff`. |
| **Transporte** | En producción (Render.com) el tráfico se sirve sobre **HTTPS** con certificado gestionado por la plataforma. |

### Gestión de secretos

- `SECRET_KEY`, `OPENAI_API_KEY`, credenciales de base de datos y de correo se
  leen de **variables de entorno** (archivo `.env`, cargado con
  `python-dotenv`). El `.env` está fuera del control de versiones; el
  repositorio solo incluye `env.sample` como plantilla.
- La API REST generada por `apps.dyn_api` usa Django REST Framework con
  autenticación por **sesión o token** (`rest_framework.authtoken`).

## Aplicación de escritorio (sin ORM)

La app de escritorio **no usa el ORM de Django**: habla SQL directo contra
PostgreSQL con `psycopg2` (`backend/db_client.py`). Esto plantea una pregunta
razonable: ¿se pierde la seguridad que ofrece el ORM?

### ¿Qué seguridad da realmente el ORM?

La protección de seguridad central que aporta un ORM es la **parametrización
automática de consultas**, que elimina la inyección SQL. Pero la
parametrización **no es exclusiva del ORM**: es una capacidad del driver
(`psycopg2`) que el ORM simplemente usa por debajo.

### Cómo se protege la app de escritorio

Todas las consultas de `db_client.py` usan **consultas parametrizadas**: el SQL
contiene marcadores `%s` y los valores se pasan como tupla separada. El driver
envía el SQL y los datos por canales distintos, de modo que un valor jamás se
interpreta como código SQL:

```python
# Así se escribe SIEMPRE en db_client.py (seguro):
cur.execute(
    "UPDATE pages_eegsession SET ended_at=%s, dominant_emotion=%s WHERE id=%s",
    (ended_at, dominant_emotion, session_id),
)

# Esto sería inyectable y NUNCA se hace en el proyecto:
cur.execute(f"UPDATE pages_eegsession SET ended_at='{ended_at}' WHERE id={session_id}")
```

Es decir: **la app de escritorio tiene la misma protección contra inyección
SQL que el ORM**, porque usa el mismo mecanismo (parametrización del driver),
solo que de forma explícita en lugar de automática.

Además:

- Las credenciales de la base de datos viven en un `settings.json` **local**
  (creado a partir de `settings.example.json`), no incrustadas en el código
  distribuido.
- La conexión usa `connect_timeout` y las escrituras corren en un hilo
  separado: un fallo de red no corta la sesión de captura y cada sesión se
  respalda localmente como JSON.

### ¿Es mala práctica no usar el ORM aquí?

Es un **compromiso deliberado**, no un descuido:

- Usar el ORM exigiría **empaquetar el proyecto Django completo** (settings,
  apps, migraciones) dentro del ejecutable de escritorio, inflando el `.exe` y
  acoplando ambas aplicaciones a nivel de código.
- La app de escritorio solo necesita **cinco consultas fijas** sobre tres
  tablas; no construye SQL dinámico a partir de entradas del usuario.
- El esquema sigue siendo **propiedad de Django**: la web define los modelos y
  las migraciones, y la app de escritorio respeta las tablas generadas
  (`pages_eegsession`, `pages_eegreading`, `pages_patient`).

Lo que sí se pierde al no usar el ORM — y cómo se mitiga:

| Se pierde | Mitigación en este proyecto |
|---|---|
| Validación a nivel de modelo | Las lecturas provienen del pipeline interno (Neurosky → CNN), no de entrada libre del usuario; los tipos los valida PostgreSQL. |
| Migraciones automáticas | Solo Django migra el esquema; la app de escritorio es un consumidor de solo lectura/escritura de tablas ya existentes. |
| Abstracción del nombre de tablas | Los nombres siguen la convención fija de Django (`app_label + modelo`) y están centralizados en `db_client.py`. |

## Limitaciones conocidas

Como todo proyecto, hay aspectos que quedarían por endurecer en un despliegue
de mayor escala:

- La app de escritorio se conecta **directamente** a PostgreSQL con un usuario
  de base de datos; una evolución natural sería exponer una API REST
  autenticada en la web y que el escritorio escriba a través de ella.
- `ALLOWED_HOSTS` es permisivo en la configuración actual; en producción
  conviene restringirlo al dominio real.
- No hay limitación de tasa (*rate limiting*) en los endpoints JSON internos;
  están protegidos por sesión pero no contra abuso de un usuario autenticado.

← Volver al [índice](README.md).
