# 07 · Aplicación de Escritorio EEG

La aplicación de escritorio (`EEGDesktopApp`) captura la señal EEG de la diadema
**Neurosky Mindwave Mobile 2**, la procesa en tiempo real, clasifica la emoción del
paciente con una red neuronal y guarda la sesión en la base de datos compartida.

## ¿Por qué una app de escritorio y no web?

- El navegador **no puede** abrir puertos serie/Bluetooth por seguridad.
- La inferencia con TensorFlow se ejecuta **localmente** en tiempo real.

## Arquitectura: pywebview

`pywebview` muestra una interfaz **HTML/CSS/JS** dentro de una ventana nativa, pero
la lógica corre en **Python**. El puente entre ambos mundos es el objeto `Api`:

```
┌──────────────────────────────────────────────────────────┐
│  Ventana pywebview                                         │
│  ┌────────────────────────┐   window.pywebview.api.*      │
│  │ Frontend (HTML/JS)      │ ───────────────────────────► │
│  │ dashboard, sesiones,    │                              │
│  │ configuración           │ ◄─────────────────────────── │
│  └────────────────────────┘      (respuestas JSON)        │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Backend (Python) — clase Api (backend/api.py)      │  │
│  │  • EEGConnector      (lectura Neurosky)            │  │
│  │  • feature_extractor (EEG → 2548 features)         │  │
│  │  • EmotionPredictor  (CNN + heurística)            │  │
│  │  • SessionManager    (grabación de sesiones)       │  │
│  │  • db_client         (PostgreSQL directo)          │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

El punto de entrada es `main.py`, que crea la ventana y le inyecta la instancia de
`Api` como `js_api`.

## Componentes del backend

| Archivo | Responsabilidad |
|---|---|
| `backend/api.py` | Clase `Api`: expone métodos al frontend (`get_realtime_data`, `connect_device`, `start_session`, `stop_session`, `get_model_info`, `get_diagnostics`, …). Orquesta todo. |
| `backend/eeg_connector.py` | Abre el puerto COM y decodifica el protocolo ThinkGear en un hilo. Ver [doc 08](08-neurosky-thinkgear.md). |
| `backend/feature_extractor.py` | Convierte el EEG crudo + potencias de banda en un vector de 2548 características. Ver [doc 09](09-procesamiento-senal.md). |
| `backend/emotion_predictor.py` | Carga la CNN (`.h5`) + el scaler y ejecuta la inferencia. Tiene una heurística de respaldo. Ver [doc 10](10-modelo-cnn-emociones.md). |
| `backend/session_manager.py` | Controla el ciclo de vida de una grabación y persiste lecturas. Ver [doc 11](11-integracion-datos.md). |
| `backend/db_client.py` | Conexión `psycopg2` directa a `ceredb`. |

## El bucle en tiempo real

El frontend hace *polling* cada ~200 ms llamando a `get_realtime_data()`. En cada
llamada, el backend:

1. Toma el último paquete parseado del dispositivo (`get_latest()`) y el buffer de
   señal cruda (`raw_buffer`).
2. Calcula las potencias de banda para mostrar (delta, theta, alpha, beta, gamma).
3. Si hay suficiente señal cruda (≥ 64 muestras):
   - Extrae el vector de características.
   - Ejecuta la CNN (`EmotionPredictor.predict`) → emoción + confianza.
   - Si el modelo aún está cargando, usa la **heurística** de respaldo.
4. Si hay una sesión activa, guarda la lectura (en un hilo, para no bloquear).
5. Devuelve al frontend todo lo necesario para pintar: forma de onda, potencias,
   emoción, atención/meditación, estado de la sesión y **diagnóstico de conexión**.

```python
if len(raw_buf) >= 64:
    if self._predictor:                        # CNN cargada
        feat = extract_features(raw_buf, pkt)
        emotion = self._predictor.predict(feat)
    else:                                      # aún cargando TensorFlow
        emotion = EmotionPredictor.heuristic(pkt, att, med)
```

## Carga del modelo en segundo plano

TensorFlow tarda ~30 s en importarse. Para que la ventana abra al instante, el
modelo se carga en un **hilo daemon** (`threading.Thread(target=self._load_model)`).
Mientras tanto, la heurística cubre las predicciones.

## Interfaz (frontend)

| Página | Contenido |
|---|---|
| `dashboard.html` | Señal EEG cruda, estado emocional (con precisión del modelo y etiqueta "estimado"), potencias de banda, atención/meditación, estado de datos del dispositivo. |
| `sessions.html` | Historial de sesiones grabadas. |
| `settings.html` | Selección de puerto COM, datos del operador y conexión a la base de datos. |

Continúa en → [08 · Neurosky y el Protocolo ThinkGear](08-neurosky-thinkgear.md).
