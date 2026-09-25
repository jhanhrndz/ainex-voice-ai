# =========================================================
# CONFIGURACIÓN PRINCIPAL
# =========================================================

NOMBRE_ROBOT = "Nelson"        # Cambiar nombre del robot 
WAKE_WORD_THRESHOLD = 70       # score mínimo (0-100) de similitud para aceptar el wake word

MODEL_SIZE = "small"           # "small", "medium", "large-v3-turbo" — ajusta según tu benchmark de latencia
COMPUTE_TYPE = "float16"       # float16 en GPU CUDA para máxima aceleración de núcleos Tensor
DEVICE_WHISPER = "cuda"        # Intentar ejecutar en GPU por defecto con fallback a CPU

INTENT_THRESHOLD = 75          # score mínimo para aceptar una intención
AMBIGUEDAD_MARGEN = 8          # si el 2do mejor candidato está a menos de esto del 1ro -> ambiguo
PARAR_THRESHOLD = 70           # con fuzz.ratio sobre texto ya limpio de wake word, este umbral es más seguro

NO_SPEECH_PROB_MAX = 0.6       # filtro de confianza Whisper: por encima de esto, probablemente no hay voz
AVG_LOGPROB_MIN = -1.0         # por debajo de esto, la transcripción es poco confiable

SAMPLE_RATE = 16000
VAD_FRAME_SAMPLES = 512        # 32ms a 16kHz — tamaño de chunk requerido por Silero VAD
MAX_DURACION_SEGMENTO_SEG = 7.0  # corte forzado si el VAD no detecta silencio limpio (ruido/voces cruzadas)
GOOGLE_TIMEOUT_SEG = 7.0         # tiempo máximo de espera por Google antes de usar el resultado de Whisper
MAX_ANTIGUEDAD_SEGMENTO_SEG = 6.0  # si un segmento lleva más de esto en cola sin procesar, se descarta

INITIAL_PROMPT = (
    f"{NOMBRE_ROBOT}, saluda, baila, patea, camina, adelante, atrás, "
    "izquierda, derecha, explora, navega, describe, qué ves, "
    "para, detente, alto, firmes, listo, levántate, mano, alza"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5vl:3b"

# Detección automática de IP con fallback a 192.168.149.1 (estilo ORION)
DIR_IP = '192.168.149.1'
ROBOT_PORT = 9000

# Control de inactividad para vigilancia facial
TIEMPO_INACTIVIDAD_MAX = 45 #Segundos
