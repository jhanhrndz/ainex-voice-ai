import os
import sys
import time
import queue
import threading
import warnings

# Inyectar paths de NVIDIA antes de cargar cualquier otra librería (Torch/Whisper)
_venv_base = sys.prefix
_cublas_bin = os.path.join(_venv_base, 'Lib', 'site-packages', 'nvidia', 'cublas', 'bin')
_cudnn_bin = os.path.join(_venv_base, 'Lib', 'site-packages', 'nvidia', 'cudnn', 'bin')
if os.path.exists(_cublas_bin):
    if hasattr(os, 'add_dll_directory'): os.add_dll_directory(_cublas_bin)
    os.environ['PATH'] = _cublas_bin + ';' + os.environ.get('PATH', '')
if os.path.exists(_cudnn_bin):
    if hasattr(os, 'add_dll_directory'): os.add_dll_directory(_cudnn_bin)
    os.environ['PATH'] = _cudnn_bin + ';' + os.environ.get('PATH', '')

warnings.filterwarnings("ignore")

from config.settings import NOMBRE_ROBOT, TIEMPO_INACTIVIDAD_MAX, MAX_ANTIGUEDAD_SEGMENTO_SEG
from config.intents import COMANDO_SOCKET
from core.audio_capture import AudioCapture
from core.stt_engine import STTEngine
from core.nlp_engine import NLPEngine
from core.tts_engine import TTSEngine
from llm.ollama_client import OllamaClient
from robot.robot_client import RobotClient
from robot.vision import RobotVision
from core.vigilancia_facial_yunet import ejecutar_ronda_vigilancia_yunet

# Control global
app_activa = True
comando_cola = queue.Queue()
segmentos_pendientes = queue.Queue()
modo_exploracion_evento = threading.Event()
detener_evento = threading.Event()
ultimo_tiempo_comando = time.time()

# Instanciar motores
robot_client = RobotClient()
vision_client = RobotVision(robot_client)
tts = TTSEngine()
stt = STTEngine()
nlp = NLPEngine()
llm = OllamaClient()
audio_capture = AudioCapture(segmentos_pendientes)

def procesar_audio_capturado(audio_bytes):
    texto, motor_usado = stt.transcribir_audio(audio_bytes)
    if not texto:
        print("🙉 [Descartado: silencio o baja confianza]")
        return

    print(f"🎙️ [AUDIO ESCUCHADO vía {motor_usado}]: \"{texto}\"")
    texto_norm = nlp.normalizar_texto(texto)

    tiene_wake, palabra_wake = nlp.contiene_wake_word(texto_norm)
    if not tiene_wake:
        print(f"🙉 [Ignorado, sin wake word '{NOMBRE_ROBOT}']: \"{texto}\"")
        return

    texto_comando = nlp.quitar_wake_word(texto_norm, palabra_wake)

    if nlp.es_orden_de_parar(texto_comando):
        print("🛑 [ORDEN DE PARADA INMEDIATA] Deteniendo robot...")
        modo_exploracion_evento.clear()
        detener_evento.set()
        robot_client.enviar_comando("parar")
        return

    intent_id, score, ambiguo = nlp.clasificar_intencion(texto_comando)

    if intent_id is None:
        print(f"❓ [Sin intención reconocida] (mejor score: {score:.1f}) texto: \"{texto_comando}\"")
        tts.speak("No entendí ese comando, ¿puedes repetirlo?")
        return

    if ambiguo:
        print(f"⚠️ [Comando ambiguo] intent candidato: {intent_id} (score {score:.1f})")
        tts.speak("No estoy seguro de tu comando, ¿puedes repetirlo?")
        return

    print(f"✨ [INTENCIÓN ACEPTADA]: {intent_id} (score {score:.1f})")
    comando_cola.put(intent_id)

def hilo_procesamiento_voz():
    while app_activa:
        try:
            audio_bytes, timestamp_captura = segmentos_pendientes.get(timeout=0.5)
        except queue.Empty:
            continue

        antiguedad = time.time() - timestamp_captura
        if antiguedad > MAX_ANTIGUEDAD_SEGMENTO_SEG:
            print(f"🗑️ [Descartado por antigüedad] segmento de hace {antiguedad:.1f}s")
            continue

        procesar_audio_capturado(audio_bytes)

def hilo_exploracion():
    print("🚀 [EXPLORACIÓN] Hilo de exploración iniciado.")
    while modo_exploracion_evento.is_set() and not detener_evento.is_set():
        print("📷 Escaneando 3 vistas panorámicas...")
        panorama_ruta = vision_client.capturar_tres_fotos(detener_evento)
        if panorama_ruta and os.path.exists(panorama_ruta) and not detener_evento.is_set():
            imagen_b64 = vision_client.convertir_imagen_a_base64(panorama_ruta)
            direccion = llm.preguntar_direccion(imagen_b64)
            if direccion != "error" and not detener_evento.is_set():
                print(f"👉 Dirección sugerida por IA: {direccion.upper()}")
                robot_client.enviar_comando(direccion)
                time.sleep(3.5)
        
        if modo_exploracion_evento.is_set() and not detener_evento.is_set():
            time.sleep(0.5)
    print("🛑 [EXPLORACIÓN] Hilo de exploración finalizado.")

def main():
    global app_activa, ultimo_tiempo_comando
    
    print("\n=======================================================")
    print(f"🤖 SISTEMA DE CONTROL POR VOZ E IA LOCAL ({NOMBRE_ROBOT}) - v2.0 Clean Architecture")
    print("=======================================================")
    print(f"Palabra clave requerida: '{NOMBRE_ROBOT}' (ejemplo: '{NOMBRE_ROBOT} saluda')")
    print("=======================================================\n")

    hilo_audio = threading.Thread(target=audio_capture.iniciar_captura, daemon=True)
    hilo_proc = threading.Thread(target=hilo_procesamiento_voz, daemon=True)
    hilo_audio.start()
    hilo_proc.start()

    tts.speak(f"Hola, soy {NOMBRE_ROBOT}. Estoy listo para tus comandos.")
    ultimo_tiempo_comando = time.time()

    try:
        thread_exploracion = None

        while True:
            if not modo_exploracion_evento.is_set():
                if (time.time() - ultimo_tiempo_comando) > TIEMPO_INACTIVIDAD_MAX:
                    def rutina_de_saludo():
                        tts.speak("¡Hola! ¡Qué gusto verte!")
                        robot_client.enviar_comando("saluda")
                        time.sleep(3.5)
                    
                    ejecutar_ronda_vigilancia_yunet(
                        robot_client, 
                        vision_client.tomar_foto, 
                        rutina_de_saludo
                    )
                    ultimo_tiempo_comando = time.time()

            try:
                intent_id = comando_cola.get(timeout=0.5)
                ultimo_tiempo_comando = time.time()
            except queue.Empty:
                if thread_exploracion is not None and not thread_exploracion.is_alive():
                    modo_exploracion_evento.clear()
                    thread_exploracion = None
                continue

            if intent_id == "parar":
                print(f"🛑 [{NOMBRE_ROBOT}]: Deteniendo robot...")
                modo_exploracion_evento.clear()
                detener_evento.set()
                robot_client.enviar_comando("parar")
                if thread_exploracion is not None and thread_exploracion.is_alive():
                    thread_exploracion.join(timeout=5)
                thread_exploracion = None
                continue

            if modo_exploracion_evento.is_set():
                print(f"⚠️ [{NOMBRE_ROBOT}]: En modo exploración. Di '{NOMBRE_ROBOT}, para' para detener primero.")
                continue

            detener_evento.clear()

            if intent_id == "explora":
                print(f"\n🚀 [{NOMBRE_ROBOT} - MODO EXPLORACIÓN ACTIVADO] Navegando con Ollama...")
                tts.speak("Modo exploración activado.")
                detener_evento.clear()
                modo_exploracion_evento.set()
                thread_exploracion = threading.Thread(target=hilo_exploracion, daemon=True)
                thread_exploracion.start()

            elif intent_id == "describe":
                panorama_ruta = vision_client.capturar_tres_fotos(detener_evento)
                if panorama_ruta and os.path.exists(panorama_ruta):
                    imagen_b64 = vision_client.convertir_imagen_a_base64(panorama_ruta)
                    desc = llm.identificar_persona(imagen_b64)
                    print(f"\n👁️ [DESCRIPCIÓN IA]: {desc}\n")
                    tts.speak(desc)
                    if os.path.exists(panorama_ruta):
                        os.remove(panorama_ruta)

            elif intent_id in COMANDO_SOCKET:
                robot_client.enviar_comando(COMANDO_SOCKET[intent_id])

            else:
                print(f"❓ [{NOMBRE_ROBOT}]: Intención desconocida: '{intent_id}'")

    except KeyboardInterrupt:
        print("\n⏹️ Interrupción por teclado")
    finally:
        app_activa = False
        audio_capture.detener()
        robot_client.cerrar()

if __name__ == "__main__":
    main()