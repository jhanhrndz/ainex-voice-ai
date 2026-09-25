import concurrent.futures
import time
import numpy as np
import speech_recognition as sr
from config.settings import MODEL_SIZE, DEVICE_WHISPER, COMPUTE_TYPE, SAMPLE_RATE, NO_SPEECH_PROB_MAX, AVG_LOGPROB_MIN, INITIAL_PROMPT, GOOGLE_TIMEOUT_SEG

class STTEngine:
    def __init__(self):
        self.usar_whisper = False
        self.modelo_whisper = None
        self._recognizer_google = sr.Recognizer()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self._cargar_whisper()

    def _cargar_whisper(self):
        try:
            from faster_whisper import WhisperModel
            try:
                self.modelo_whisper = WhisperModel(MODEL_SIZE, device=DEVICE_WHISPER, compute_type=COMPUTE_TYPE)
                print(f"[INFO] 🚀 Faster-Whisper cargado en GPU (NVIDIA CUDA, {MODEL_SIZE}, {COMPUTE_TYPE}).")
                self.usar_whisper = True
            except Exception as e_cuda:
                print(f"[ADVERTENCIA] ⚠️ GPU no disponible para Whisper ({e_cuda}). Activando fallback en CPU...")
                self.modelo_whisper = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
                print(f"[INFO] 🎙️ Faster-Whisper cargado en CPU ({MODEL_SIZE}, int8).")
                self.usar_whisper = True
        except Exception as e_import:
            print(f"[INFO] ⚠️ Error al importar Faster-Whisper: {e_import}")

    def _intentar_google(self, audio_bytes):
        try:
            audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)
            return self._recognizer_google.recognize_google(audio_data, language='es-ES').lower().strip()
        except Exception:
            return ""

    def _intentar_whisper(self, audio_bytes):
        if not (self.usar_whisper and self.modelo_whisper):
            return ""
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            segmentos_gen, _info = self.modelo_whisper.transcribe(
                audio_np,
                language="es",
                beam_size=1,
                vad_filter=False,
                condition_on_previous_text=False,
                initial_prompt=INITIAL_PROMPT,
            )
            partes_validas = []
            for seg in segmentos_gen:
                if seg.no_speech_prob > NO_SPEECH_PROB_MAX:
                    continue
                if seg.avg_logprob < AVG_LOGPROB_MIN:
                    continue
                partes_validas.append(seg.text)
            return " ".join(partes_validas).lower().strip()
        except Exception as e_whisper:
            print(f"[WHISPER ERROR]: {e_whisper}")
            return ""

    def transcribir_audio(self, audio_bytes):
        t0 = time.time()
        duracion_audio = len(audio_bytes) / 2 / SAMPLE_RATE

        future_whisper = self._executor.submit(self._intentar_whisper, audio_bytes)
        future_google = self._executor.submit(self._intentar_google, audio_bytes)

        texto = ""
        motor_usado = ""

        try:
            texto_google = future_google.result(timeout=GOOGLE_TIMEOUT_SEG)
            if texto_google:
                texto = texto_google
                motor_usado = "google"
        except concurrent.futures.TimeoutError:
            pass 

        if not texto:
            try:
                texto_whisper = future_whisper.result(timeout=20)
                if texto_whisper:
                    texto = texto_whisper
                    motor_usado = f"whisper[{MODEL_SIZE}]"
            except concurrent.futures.TimeoutError:
                print("[WHISPER TIMEOUT]: no respondió en 20s.")

        latencia_total = time.time() - t0
        if motor_usado:
            motor_usado += f" (audio {duracion_audio:.1f}s, resp {latencia_total:.2f}s)"
        return texto, motor_usado
