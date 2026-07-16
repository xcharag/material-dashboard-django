# 10 · Modelo CNN de Emociones

El corazón del monitoreo EEG es una **red neuronal convolucional (CNN)** que
clasifica la señal en una de tres emociones: **POSITIVE**, **NEUTRAL** o
**NEGATIVE**.

## Concepto: ¿qué es una CNN?

Una **CNN** (*Convolutional Neural Network*) es un tipo de red neuronal que aplica
**filtros convolucionales** que se deslizan sobre la entrada para detectar patrones
locales. Se popularizaron en imágenes (detectan bordes, texturas), pero funcionan
igual sobre señales 1D como el EEG: una **`Conv1D`** desliza un filtro a lo largo de
la secuencia de características y aprende a reconocer patrones locales relevantes.

Ventaja frente a una red totalmente conectada (densa): la CNN **comparte pesos** y
detecta patrones sin importar su posición exacta, con menos parámetros.

## El dataset

**EEG Brainwave Dataset — Feeling Emotions** (Jordan J. Bird, publicado en Kaggle).

| Propiedad | Valor |
|---|---|
| Muestras | 2132 |
| Características por muestra | 2548 |
| Clases | NEGATIVE, NEUTRAL, POSITIVE (balanceadas: 708 / 716 / 708) |
| Dispositivo original | Diadema **Muse** de 4 canales (TP9, AF7, AF8, TP10) |

El archivo `emotions.csv` se coloca en `EEGDesktopApp/seed/` para reentrenar.

## Arquitectura de la red

Definida en `models/train_cnn.py`. La entrada es el vector de 2548 características
tratado como una secuencia de forma `(2548, 1)`:

```
Input (2548, 1)
   │
Conv1D(64, kernel=3, ReLU)  →  MaxPooling1D(2)  →  SpatialDropout1D(0.3)
   │
Conv1D(64, kernel=3, ReLU)  →  MaxPooling1D(4)  →  SpatialDropout1D(0.3)
   │
Conv1D(64, kernel=3, ReLU)  →  MaxPooling1D(4)  →  SpatialDropout1D(0.3)
   │
Flatten
   │
Dense(64, ReLU)  →  Dropout(0.5)
   │
Dense(3, Softmax)   →   [P(NEGATIVE), P(NEUTRAL), P(POSITIVE)]
```

### Conceptos de la arquitectura

- **ReLU:** función de activación que introduce no linealidad (`max(0, x)`).
- **MaxPooling1D:** reduce a la mitad/cuarto la longitud quedándose con el valor
  máximo de cada ventana; resume y baja el costo de cómputo.
- **SpatialDropout1D / Dropout:** apagan aleatoriamente neuronas/mapas durante el
  entrenamiento para **evitar el sobreajuste** (*overfitting*).
- **Flatten:** aplana la salida convolucional a un vector para las capas densas.
- **Softmax:** convierte la salida final en **probabilidades** que suman 1; la clase
  con mayor probabilidad es la predicción, y ese valor es la **confianza**.

## Entrenamiento

`models/train_cnn.py` realiza:

1. **Carga** de `emotions.csv` y codificación de etiquetas con orden fijo
   (`NEGATIVE=0, NEUTRAL=1, POSITIVE=2`) — debe coincidir con el predictor.
2. **Split** entrenamiento/prueba 80/20 estratificado (`train_test_split`).
3. **Estandarización** con `StandardScaler` (z-score): se ajusta con el set de
   entrenamiento y se guarda en `scaler.pkl`.
4. **Reshape** a `(muestras, 2548, 1)` para la `Conv1D`.
5. **Entrenamiento** con Adam (LR 5e-4), pérdida
   `sparse_categorical_crossentropy`, hasta 120 épocas con:
   - **EarlyStopping** (paciencia 15, restaura los mejores pesos).
   - **ReduceLROnPlateau** (baja el LR si se estanca).
6. **Evaluación** sobre el set de prueba y **guardado** de artefactos.

### Concepto: estandarización (StandardScaler)

Cada característica se transforma a media 0 y desviación 1:
`z = (x − media) / desviación`. Esto ayuda a que la red entrene de forma estable. El
**mismo** scaler ajustado en entrenamiento debe aplicarse en inferencia, por eso se
persiste en `scaler.pkl`.

## Resultados

| Métrica | Valor |
|---|---|
| **Precisión en prueba (test accuracy)** | **97.66 %** |
| Pérdida en prueba | 0.0932 |
| Muestras entrenamiento / prueba | 1705 / 427 |

Estos valores se guardan en `models/metrics.json` y se muestran en el dashboard como
**"CNN (Conv1D) · 97.7 % precisión"**.

> **Nota metodológica:** la primera versión usó `GlobalAveragePooling` +
> `BatchNormalization` y sufrió sobreajuste severo (entrenamiento 95 %, validación
> 40 %). Cambiar a `Flatten` + `SpatialDropout1D` y quitar `BatchNorm` resolvió la
> generalización. Es un ejemplo de cómo se iteró la arquitectura del modelo
> durante el desarrollo.

## Artefactos generados

| Archivo | Contenido |
|---|---|
| `models/eeg_emotion_model.h5` | La CNN entrenada (Keras/HDF5). |
| `models/scaler.pkl` | `StandardScaler` ajustado (pickle). |
| `models/metrics.json` | Precisión de prueba + metadatos (mostrado en la UI). |

## Inferencia en tiempo real

`backend/emotion_predictor.py`:

1. Recibe el vector de 2548 características.
2. Lo escala con `scaler.pkl`.
3. Detecta que el modelo espera 3 dimensiones y hace *reshape* a `(1, 2548, 1)`.
4. Ejecuta la CNN → probabilidades softmax.
5. Devuelve `{label, confidence, probs, color, estimated: True}`.

El campo **`estimated: True`** indica que la entrada proviene de la Neurosky
(1 canal) y difiere de los datos de entrenamiento (Muse, 4 canales); por eso la UI
añade "estimado" a la confianza.

## Heurística de respaldo

Mientras TensorFlow carga (~30 s), se usa `EmotionPredictor.heuristic()`: una regla
simple basada en la razón entre potencias alpha+beta y delta+theta y los índices
eSense de atención/meditación. Devuelve la misma estructura pero con
`probs = [0, 0, 0]`, lo que permite distinguir en el frontend si está activa la CNN
(probabilidades reales) o la heurística.

Continúa en → [11 · Integración de Datos EEG ↔ Web](11-integracion-datos.md).
