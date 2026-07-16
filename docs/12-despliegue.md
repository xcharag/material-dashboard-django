# 12 · Despliegue

## Aplicación web (Django)

### Ejecución local (desarrollo)

```bash
# 1. Crear entorno y dependencias
pip install -r requirements.txt

# 2. Variables de entorno: copiar env.sample a .env y completar
#    DEBUG, SECRET_KEY, OPENAI_API_KEY, credenciales de base de datos, correo…

# 3. Base de datos
python manage.py migrate

# 4. Usuario administrador
python manage.py createsuperuser

# 5. Servidor
python manage.py runserver     # http://127.0.0.1:8000
```

Si no se define `DB_ENGINE`, Django usa **SQLite** localmente. Para PostgreSQL se
configuran `DB_ENGINE=postgresql`, `DB_HOST`, `DB_NAME`, `DB_USERNAME`, `DB_PASS`,
`DB_PORT`.

### Variables de entorno principales (`.env`)

| Variable | Uso |
|---|---|
| `DEBUG` | `True` en desarrollo, `False` en producción. |
| `SECRET_KEY` | Clave secreta de Django. |
| `OPENAI_API_KEY` | Acceso a la API de OpenAI (módulo de IA). |
| `DB_*` | Conexión a PostgreSQL. |
| `EMAIL_*` | SMTP para recuperación de contraseña. |

### Producción

| Herramienta | Rol |
|---|---|
| **Gunicorn** | Servidor WSGI (`gunicorn-cfg.py`, enlaza `0.0.0.0:5005`). |
| **WhiteNoise** | Sirve archivos estáticos sin un servidor aparte. |
| **Docker Compose** | Django + Nginx como *reverse proxy* (puerto 5085). |
| **Render.com** | `render.yaml` + `build.sh` (pip install, collectstatic, migrate). |

Recolección de estáticos antes de desplegar:

```bash
python manage.py collectstatic --no-input
```

> **Recordatorio:** tras añadir librerías estáticas nuevas (por ejemplo
> `apexcharts.min.js`), hay que volver a ejecutar `collectstatic` para que se sirvan
> en producción.

## Aplicación de escritorio (EEG)

### Ejecución local

```bash
cd EEGDesktopApp
pip install -r requirements.txt
python main.py
```

Requisitos previos:

- **Diadema emparejada** por Bluetooth (aparecerá como puerto COM, p. ej. `COM5`).
- `settings.json` con las credenciales de la base de datos compartida (se crea a
  partir de `settings.example.json`).

### Reentrenar el modelo CNN

```bash
# Colocar el dataset en seed/emotions.csv, luego:
python models/train_cnn.py
# Genera: eeg_emotion_model.h5, scaler.pkl, metrics.json
```

### Empaquetado a `.exe` (PyInstaller)

La app se distribuye como ejecutable de Windows. El empaquetado incluye la carpeta
`frontend/` y `models/` como datos (`--add-data`). El instalador resultante se
comprime como `EEGMonitor_Setup.zip` y se publica para descarga desde la web.

En `main.py`, la ruta base se resuelve con `sys._MEIPASS` cuando corre empaquetado,
de modo que encuentra `frontend/index.html` dentro del `.exe`.

## Hosting de esta documentación

Los archivos Markdown se leen directamente en GitHub. Para una **página web
navegable** (con menú lateral y buscador) usa **MkDocs** con el tema Material,
configurado en `mkdocs.yml` (raíz del repositorio):

```bash
pip install mkdocs mkdocs-material

mkdocs serve       # vista previa en http://127.0.0.1:8000
mkdocs build       # genera un sitio estático en site/
mkdocs gh-deploy   # publica en GitHub Pages (rama gh-pages)
```

Con `gh-deploy`, la documentación queda accesible en una URL pública
(`https://<usuario>.github.io/<repo>/`) desde cualquier dispositivo, sin
necesidad de clonar el repositorio.

### Alternativas de hosting

- **GitHub Pages** (gratis, vía `mkdocs gh-deploy`).
- **Netlify / Vercel** apuntando a la carpeta `site/` generada.
- **Read the Docs** conectando el repositorio.
- Simplemente navegar la carpeta `docs/` en GitHub (sin build).

Continúa en → [13 · Glosario Técnico](13-glosario.md).
