# 📖 Referencia de API y Módulos del Sistema

Este documento contiene la especificación detallada de las clases, funciones, parámetros y valores de retorno de los módulos implementados en `pc_client/`.

---

## 1. Módulo `config`

### `config.settings`
Define los parámetros de ajuste del sistema, umbrales y conexiones.

- `NOMBRE_ROBOT` (*str*): Nombre del robot y Wake Word principal (por defecto: `"Nelson"`).
- `WAKE_WORD_THRESHOLD` (*int*): Similitud mínima (0–100) aceptada para el wake word (`70`).
- `MODEL_SIZE` (*str*): Variante de Faster-Whisper a cargar (`"small"`).
- `COMPUTE_TYPE` (*str*): Precisión numérica en GPU (`"float16"`).
- `DEVICE_WHISPER` (*str*): Dispositivo preferente para inferencia (`"cuda"` con fallback automático a `"cpu"`).
- `INTENT_THRESHOLD` (*int*): Umbral mínimo de puntuación difusa para clasificar intención (`75`).
- `AMBIGUEDAD_MARGEN` (*int*): Diferencia mínima requerida entre el 1° y 2° mejor candidato para descartar ambigüedad (`8`).
- `SAMPLE_RATE` (*int*): Frecuencia de muestreo de captura PCM (`16000` Hz).
- `VAD_FRAME_SAMPLES` (*int*): Tamaño de ventana para Silero VAD (`512` muestras / 32 ms).
- `TIEMPO_INACTIVIDAD_MAX` (*int*): Segundos sin comandos antes de activar el patrullaje de vigilancia facial (`45`).
- `DIR_IP` (*str*): Dirección IP del robot AiNex en la red local.
- `ROBOT_PORT` (*int*): Puerto TCP del servidor de control del robot (`9000`).

---

## 2. Módulo `core`

### `core.audio_capture.AudioCapture`
Maneja la captura de micrófono en hardware y la segmentación temporal de voz con Silero VAD.

#### Métodos:
- `__init__(segmentos_pendientes_queue: queue.Queue)`
  - *Parámetros:* Cola de destino donde se depositarán los segmentos de voz procesados `(bytes, timestamp)`.
- `iniciar_captura() -> None`
  - Abre el flujo `sounddevice.RawInputStream` en bucle concurrente no bloqueante. Emite tensores al iterador Silero VAD y detecta los eventos `start` y `end`.
- `detener() -> None`
  - Marca la bandera de finalización para cerrar limpiamente el stream de audio.

---

### `core.stt_engine.STTEngine`
Motor híbrido de conversión de voz a texto.

#### Métodos:
- `__init__()`
  - Inicializa el modelo `faster_whisper.WhisperModel` en GPU CUDA (o fallback en CPU) y un `ThreadPoolExecutor` con 4 trabajadores.
- `transcribir_audio(audio_bytes: bytes) -> tuple[str, str]`
  - Envía la tarea en paralelo a Google Speech Recognition y Faster-Whisper.
  - *Retorna:* `(texto_transcrito, motor_usado)`. Ejemplo: `("nelson saluda", "google (audio 1.5s, resp 0.42s)")`.

---

### `core.nlp_engine.NLPEngine`
Procesamiento lingüístico, normalización fonética y clasificación de intenciones.

#### Métodos:
- `normalizar_texto(texto: str) -> str`
  - *Estático.* Convierte a minúsculas, elimina signos de puntuación, tildes (descomposición NFD) y colapsa espacios.
- `contiene_wake_word(texto_norm: str) -> tuple[bool, str | None]`
  - Evalúa cada palabra contra `NOMBRE_ROBOT` usando `fuzz.ratio`.
  - *Retorna:* `(True, palabra_coincidente)` si supera `WAKE_WORD_THRESHOLD`.
- `quitar_wake_word(texto_norm: str, palabra_detectada: str) -> str`
  - Remueve el wake word detectado para aislar el comando de acción puro.
- `clasificar_intencion(texto_norm: str) -> tuple[str | None, float, bool]`
  - Compara la frase contra el corpus canónico mediante `process.extract` con `fuzz.WRatio`.
  - *Retorna:* `(intent_id, score, es_ambiguo)`.
- `es_orden_de_parar(texto_norm: str) -> bool`
  - Chequeo de seguridad con `fuzz.ratio` contra variantes de parada para evitar falsos positivos por substrings.

---

### `core.tts_engine.TTSEngine`
Síntesis de voz asíncrona hacia los altavoces locales.

#### Métodos:
- `speak(texto: str) -> None`
  - Despacha en un hilo demonio (`daemon=True`) la reproducción del texto utilizando la API nativa de Windows `SAPI.SpVoice` con fallback a `pyttsx3`.

---

### `core.vigilancia_facial_yunet`
Módulo de detección facial con OpenCV YuNet ONNX.

#### Funciones:
- `detectar_rostro_en_imagen(ruta_imagen: str) -> tuple[bool, int, float]`
  - Ejecuta la red neuronal convolucional sobre la imagen especificada.
  - *Retorna:* `(hay_rostro, numero_rostros, tiempo_ms)`.
- `ejecutar_ronda_vigilancia_yunet(controlador, funcion_tomar_foto, funcion_saludar) -> None`
  - Inclina la cámara hacia arriba, inspecciona las posiciones `['izquierda', 'centro', 'derecha']` y ejecuta la rutina de saludo si encuentra al menos un rostro humano.

---

## 3. Módulo `llm`

### `llm.ollama_client.OllamaClient`
Cliente HTTP para el servidor de inferencia local Ollama ejecutando `qwen2.5vl:3b`.

#### Métodos:
- `consultar(prompt: str, imagen_base64: str, temperature=0.0, num_predict=10, stop=None) -> str`
  - Envía la solicitud multimodal a `/api/generate`.
- `preguntar_direccion(imagen_base64: str) -> str`
  - *Perfil Estricto de Navegación:* `temperature=0.0`, `num_predict=10`, `stop=["\n", "."]`.
  - Analiza el piso en el panorama tri-seccional y responde estrictamente `"adelante"`, `"izquierda"`, `"derecha"` o `"atras"`.
- `identificar_persona(imagen_base64: str) -> str`
  - *Perfil Descriptivo:* `temperature=0.3`, `num_predict=80`, `stop=[]`.
  - Genera una descripción natural en español de la escena visible frente al robot.

---

## 4. Módulo `robot`

### `robot.robot_client.RobotClient`
Cliente de sockets TCP con Keep-Alive y reintentos.

#### Métodos:
- `enviar_comando(direccion: str) -> None`
  - Envía `<direccion>\n` con reconexión automática transparente.
- `mover_camara(posicion: str) -> None`
  - Envía `servo_<posicion>\n` y espera 1.2 segundos para la estabilización inercial del cuello.
- `inclinar_camara(inclinacion: str) -> None`
  - Envía `servo_<inclinacion>\n` (ej: `arriba`, `frente`).
- `cerrar() -> None`
  - Cierra de forma segura el descriptor del socket.

---

### `robot.vision.RobotVision`
Manipulación de imagen y captura desde la cámara IP de ROS.

#### Métodos:
- `tomar_foto(nombre_archivo: str) -> str | None`
  - Adquiere un fotograma nítido desde el stream MJPEG.
- `capturar_tres_fotos(detener_evento: threading.Event) -> str | None`
  - Ejecuta el ciclo motor de cuello (izq, centro, der), captura los 3 frames, aplica **CLAHE** y ensambla el panorama cuadrado de 960x960 px.
- `convertir_imagen_a_base64(ruta_imagen: str) -> str`
  - *Estático.* Codifica la imagen binaria en string base64 para el payload del VLM.
