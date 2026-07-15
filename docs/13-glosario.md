# 13 · Glosario Técnico

Definiciones breves de los términos usados en esta documentación, pensadas para
responder preguntas durante la defensa.

## Inteligencia artificial y aprendizaje automático

**CNN (Convolutional Neural Network).** Red neuronal que aplica filtros
convolucionales para detectar patrones locales. Aquí se usa `Conv1D` sobre la señal
EEG. Ver [doc 10](10-modelo-cnn-emociones.md).

**Conv1D.** Capa convolucional unidimensional: un filtro se desliza a lo largo de una
secuencia (la señal) detectando patrones locales.

**ReLU.** Función de activación `max(0, x)`; introduce no linealidad de forma barata.

**Softmax.** Función que convierte los valores de salida en probabilidades que suman
1. La clase con mayor probabilidad es la predicción; ese valor es la **confianza**.

**MaxPooling.** Operación que reduce la longitud de la señal quedándose con el máximo
de cada ventana; resume y abarata el cómputo.

**Dropout / SpatialDropout1D.** Técnica de regularización que apaga neuronas o mapas
al azar durante el entrenamiento para evitar el **sobreajuste**.

**Sobreajuste (overfitting).** Cuando el modelo memoriza el set de entrenamiento y
generaliza mal a datos nuevos (alta precisión en entrenamiento, baja en prueba).

**Épocas (epochs).** Número de pasadas completas sobre el set de entrenamiento.

**EarlyStopping.** Detiene el entrenamiento cuando la métrica de validación deja de
mejorar y restaura los mejores pesos.

**StandardScaler / z-score.** Estandarización que lleva cada característica a media 0
y desviación 1: `z = (x − media) / desviación`.

**Accuracy (precisión de prueba).** Porcentaje de aciertos del modelo sobre datos que
no vio durante el entrenamiento (set de prueba). Aquí: 97.66 %.

**Dataset.** Conjunto de datos etiquetados usado para entrenar/evaluar. Aquí, "EEG
Brainwave — Feeling Emotions".

**Heurística.** Regla simple hecha a mano (no aprendida) usada como respaldo cuando el
modelo no está disponible.

## Procesamiento de señal

**EEG (Electroencefalografía).** Registro de la actividad eléctrica del cerebro
mediante electrodos en el cuero cabelludo.

**Fp1.** Posición del electrodo en la frente (lóbulo frontal izquierdo) según el
sistema internacional **10-20** de colocación de electrodos.

**FFT (Fast Fourier Transform).** Algoritmo que descompone una señal del dominio del
tiempo al dominio de la frecuencia, revelando cuánta energía hay en cada frecuencia.

**Potencia de banda.** Energía de la señal dentro de un rango de frecuencia
(delta, theta, alpha, beta, gamma).

**Filtro pasa-banda / FIR.** Filtro que deja pasar solo un rango de frecuencias. FIR
(*Finite Impulse Response*) es un tipo de filtro digital estable.

**Ventana deslizante.** Segmento de longitud fija que recorre la señal con un paso
determinado, permitiendo analizar su evolución temporal.

**Skew (asimetría) / Kurtosis (curtosis).** Estadísticas que describen la forma de la
distribución de una señal (asimetría y "picudez").

**Muestreo (512 Hz).** Número de muestras por segundo que digitaliza el dispositivo.

## Dispositivo Neurosky

**Neurosky Mindwave Mobile 2.** Diadema EEG de un solo canal usada en el proyecto.

**ThinkGear.** Protocolo binario y chip de Neurosky que entrega EEG crudo, potencias
de banda y métricas eSense por Bluetooth.

**eSense (Atención / Meditación).** Métricas propietarias de Neurosky (0–100) que
estiman concentración y relajación.

**Poor signal.** Indicador de calidad de contacto del electrodo (0 = buena,
200 = fuera de la cabeza).

**Checksum.** Byte de verificación que confirma que un paquete no llegó corrupto.

**Baudios (57600).** Velocidad de transmisión del puerto serie.

**COM / SPP / RFCOMM.** Puerto serie virtual que Windows crea para tunelizar datos
serie sobre Bluetooth. `ERROR_SEM_TIMEOUT` (121) suele indicar el puerto equivocado.

## Web y backend

**Django.** Framework web de Python usado para la aplicación de gestión clínica.

**ORM (Object-Relational Mapping).** Capa que permite manipular la base de datos con
objetos Python en lugar de SQL crudo. Django lo provee.

**Migración.** Archivo que describe cambios en el esquema de la base de datos
generado a partir de los modelos.

**pywebview.** Librería que muestra HTML/JS en una ventana nativa y lo conecta con
Python; base de la app de escritorio.

**psycopg2.** Driver de PostgreSQL para Python; la app de escritorio lo usa para SQL
directo.

**PostgreSQL / ceredb.** Motor de base de datos y nombre de la base compartida entre
ambas aplicaciones.

**Gunicorn.** Servidor de aplicaciones WSGI para producción.

**WhiteNoise.** Sirve archivos estáticos directamente desde Django.

**PyInstaller.** Empaqueta la app de escritorio en un ejecutable `.exe`.

## Inteligencia artificial (web)

**RAG (Retrieval-Augmented Generation).** Técnica que recupera fragmentos relevantes
de documentos y se los pasa al modelo para generar respuestas fundamentadas. Ver
[doc 06](06-ia-analisis-pacientes.md).

**Embedding.** Vector numérico que representa el significado de un texto; textos
similares tienen vectores cercanos.

**Vector store.** Índice que guarda embeddings y permite buscar por similitud
semántica.

**file_search.** Herramienta de OpenAI que consulta un vector store para recuperar
fragmentos relevantes antes de responder.

**Responses / Conversations API.** APIs de OpenAI para generar respuestas y mantener
el historial de conversación del lado del servidor.

**Token.** Unidad mínima de texto (parte de palabra) que procesan los modelos de
lenguaje; determina costo y límites de contexto.

← Volver al [índice](README.md).
