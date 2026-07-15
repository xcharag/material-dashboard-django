# 08 · Neurosky y el Protocolo ThinkGear

## El dispositivo: Neurosky Mindwave Mobile 2

Es una diadema EEG de **un solo canal**. Su electrodo seco se apoya en la frente,
en la posición **Fp1** (lóbulo frontal izquierdo, según el sistema internacional
10-20 de colocación de electrodos). Una pinza en la oreja actúa como referencia/
tierra.

El chip **ThinkGear** de Neurosky hace el trabajo pesado a bordo:

- Digitaliza la señal cruda a **~512 Hz** (512 muestras por segundo).
- Calcula 8 **potencias de banda** por hardware.
- Calcula dos índices propietarios **eSense**: Atención y Meditación.
- Envía todo por Bluetooth como un flujo binario a **57600 baudios**.

## Concepto: ondas cerebrales y bandas de frecuencia

La actividad eléctrica del cerebro se descompone en bandas de frecuencia, cada una
asociada a estados mentales:

| Banda | Frecuencia | Asociada típicamente a |
|---|---|---|
| **Delta** (δ) | 1–4 Hz | Sueño profundo. |
| **Theta** (θ) | 4–8 Hz | Somnolencia, relajación profunda. |
| **Alpha** (α) | 8–13 Hz | Relajación, calma con ojos cerrados. |
| **Beta** (β) | 13–30 Hz | Concentración, alerta, pensamiento activo. |
| **Gamma** (γ) | 30–45 Hz | Procesamiento cognitivo intenso. |

Neurosky reporta 8 sub-bandas: `delta`, `theta`, `low_alpha`, `high_alpha`,
`low_beta`, `high_beta`, `low_gamma`, `mid_gamma`.

## Concepto: eSense (Atención y Meditación)

Son dos métricas propietarias de Neurosky, en escala **0–100**:

- **Atención (Attention):** nivel de concentración/foco mental.
- **Meditación (Meditation):** nivel de calma/relajación.

Se derivan del análisis de las bandas y sirven como indicadores rápidos del estado
del usuario.

## El protocolo ThinkGear (parsing)

El dispositivo envía **paquetes binarios**. `backend/eeg_connector.py` los decodifica
en un hilo en segundo plano. La estructura de un paquete es:

```
┌──────┬──────┬────────┬───────────────────────┬──────────┐
│ 0xAA │ 0xAA │ LENGTH │        PAYLOAD        │ CHECKSUM │
│ SYNC │ SYNC │        │  (LENGTH bytes)       │          │
└──────┴──────┴────────┴───────────────────────┴──────────┘
```

1. **Sincronización:** se buscan dos bytes `0xAA 0xAA` seguidos que marcan el inicio.
2. **Longitud:** el siguiente byte indica cuántos bytes tiene el *payload* (máx. 169).
3. **Payload:** contiene uno o más "data rows", cada uno con un **código** que indica
   qué dato es.
4. **Checksum:** verificación de integridad. Se calcula como
   `(~(suma de bytes del payload)) & 0xFF` y debe coincidir con el byte final; si no,
   el paquete se descarta.

### Códigos de datos relevantes

| Código | Dato | Formato |
|---|---|---|
| `0x02` | Calidad de señal (*poor signal*) | 1 byte, 0 = buena … 200 = fuera de la cabeza |
| `0x04` | Atención eSense | 1 byte (0–100) |
| `0x05` | Meditación eSense | 1 byte (0–100) |
| `0x16` | Fuerza de parpadeo | 1 byte |
| `0x80` | EEG crudo | 2 bytes, entero con signo (−32768…32767) |
| `0x83` | Potencias de banda (ASIC) | 24 bytes = 8 valores × 3 bytes big-endian |

Los códigos `< 0x80` llevan **un solo byte** de valor; los códigos `≥ 0x80` llevan
primero un byte de **longitud** y luego los datos.

### Buffer de señal cruda

Las muestras `0x80` (EEG crudo) se acumulan en un buffer circular
(`deque(maxlen=1024)`), es decir, los **últimos ~2 segundos** de señal a 512 Hz. Ese
buffer es la entrada para el extractor de características (doc 09) y para dibujar la
forma de onda.

## Diagnóstico de conexión

Un problema típico: la diadema aparece "Conectada" pero no llegan datos. Para
diagnosticarlo, el conector registra un archivo `eeg_debug.log` y expone contadores
vía `get_diagnostics()`:

- `bytes_received`, `packets_ok`, `checksum_errors`
- `raw_samples`, `attention_updates`, `meditation_updates`, `band_updates`
- `poor_signal`, `last_data_ts`

También distingue **conectado** (el puerto COM abrió) de **transmitiendo**
(`is_streaming`: llegaron datos en los últimos 3 s). El dashboard muestra
"Conectado · sin datos" cuando el puerto abrió pero no fluyen paquetes, lo que suele
indicar un puerto COM equivocado (Bluetooth suele crear dos) o la diadema apagada.

## Concepto: puertos COM sobre Bluetooth

Al emparejar la diadema, Windows crea **puertos COM virtuales** que tunelizan el
perfil serie (SPP/RFCOMM) sobre Bluetooth. Frecuentemente aparecen **dos**: uno
"saliente" que funciona y uno "entrante" que da timeout (error 121,
`ERROR_SEM_TIMEOUT`). La app lista todos los puertos con su descripción para ayudar a
elegir el correcto.

Continúa en → [09 · Procesamiento de la Señal](09-procesamiento-senal.md).
