# 09 · Procesamiento de la Señal

Antes de que la red neuronal pueda clasificar una emoción, la señal cruda de la
diadema debe transformarse en un **vector de características** con la forma que el
modelo espera: exactamente **2548 valores**. De eso se encarga
`backend/feature_extractor.py`.

## ¿Por qué 2548 características?

El modelo se entrenó con el dataset **"EEG Brainwave Dataset — Feeling Emotions"**,
donde cada muestra tiene 2548 características derivadas de la señal EEG. Para que la
diadema Neurosky pueda usar ese modelo, la app debe producir un vector del **mismo
tamaño y naturaleza**. Ver [doc 10](10-modelo-cnn-emociones.md) para el dataset.

## Concepto: dominio del tiempo vs. dominio de la frecuencia

- **Dominio del tiempo:** la señal tal cual, amplitud a lo largo del tiempo. De aquí
  salen estadísticas como media, desviación estándar, mínimo, máximo, asimetría
  (*skew*) y curtosis (*kurtosis*).
- **Dominio de la frecuencia:** cuánta energía hay en cada frecuencia. Se obtiene con
  la **Transformada Rápida de Fourier (FFT)**. Sumando la energía en cada banda
  (delta…gamma) se obtiene la "potencia de banda".

El extractor combina **ambos dominios** para cada segmento de señal.

## Concepto: canales virtuales

El dataset original se grabó con una diadema **Muse de 4 canales**. La Neurosky
tiene **1 solo canal**. Para acercar la representación, el extractor **simula 4
canales** aplicando filtros **pasa-banda FIR** a la única señal Fp1:

| Canal virtual | Banda filtrada |
|---|---|
| 1 | 1–8 Hz (delta + theta) |
| 2 | 8–13 Hz (alpha) |
| 3 | 13–30 Hz (beta) |
| 4 | 30–45 Hz (gamma) |

Un **filtro pasa-banda** deja pasar solo las frecuencias dentro de un rango y atenúa
el resto; "FIR" (*Finite Impulse Response*) es un tipo de filtro digital estable y
sencillo (`scipy.signal.firwin` + `lfilter`).

## Pipeline de extracción

```
raw_buffer (últimas ~1024 muestras a 512 Hz)
        │
        ▼
1. Normalización z-score:  raw = (raw − media) / desviación
        │
        ▼
2. 4 canales virtuales (filtros pasa-banda FIR)
        │
        ▼
3. Por canal:
     • Estadísticas globales del canal          (13 features)
     • Ventana deslizante (64 muestras, paso 32):
         para cada ventana → 13 features
        │
        ▼
4. Se añaden las 8 potencias de banda de Neurosky
        │
        ▼
5. Ajuste a 2548 valores exactos (padding o tiling + truncado)
        │
        ▼
   vector de 2548 características  ─►  scaler  ─►  CNN
```

### Las 13 características por segmento

De cada segmento de señal (`_stats_and_bands`) se calculan:

- **8 estadísticas** en el dominio del tiempo: media, desviación estándar, varianza,
  mínimo, máximo, rango (*peak-to-peak*), asimetría, curtosis.
- **5 potencias de banda** en el dominio de la frecuencia (delta, theta, alpha, beta,
  gamma), obtenidas con FFT.

### Ventana deslizante

Para capturar cómo cambia la señal a lo largo del tiempo, cada canal se recorre con
una **ventana de 64 muestras** que avanza de **32 en 32** (solapamiento del 50%). De
cada ventana se extraen las mismas 13 características. Esto genera decenas de vectores
por canal que describen la evolución temporal de la señal.

### Ajuste al tamaño exacto

Al final, el vector se **rellena o recorta** hasta tener exactamente 2548 valores
(si sobra, se trunca; si falta, se repite/tilea). Así siempre coincide con la entrada
del modelo.

## Advertencia importante: Neurosky ≠ Muse

Aunque el vector tiene el tamaño correcto, su **distribución estadística difiere** de
la del dataset de entrenamiento (Muse, 4 canales reales). Por eso las predicciones en
vivo se marcan como **"estimado"** en la interfaz: son una estimación *best-effort*,
no una clasificación de laboratorio. Este es un punto honesto y relevante para la
defensa de tesis. Detalle en [doc 10](10-modelo-cnn-emociones.md) y
[doc 11](11-integracion-datos.md).

Continúa en → [10 · Modelo CNN de Emociones](10-modelo-cnn-emociones.md).
