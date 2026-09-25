import time
import queue
import torch
import numpy as np
import sounddevice as sd
from config.settings import SAMPLE_RATE, VAD_FRAME_SAMPLES, MAX_DURACION_SEGMENTO_SEG, NOMBRE_ROBOT

class AudioCapture:
    def __init__(self, segmentos_pendientes_queue):
        self.segmentos_pendientes = segmentos_pendientes_queue
        self.modelo_vad = None
        self.vad_iterator = None
        self.app_activa = True
        self._cargar_vad()

    def _cargar_vad(self):
        print("[INFO] 🔎 Cargando Silero VAD...")
        torch.set_num_threads(1)
        self.modelo_vad, utils_vad = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            trust_repo=True,
            onnx=True
        )
        VADIterator = utils_vad[3]
        self.vad_iterator = VADIterator(
            self.modelo_vad,
            sampling_rate=SAMPLE_RATE,
            threshold=0.5,
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        )
        print("[INFO] ✅ Silero VAD listo.")

    def detener(self):
        self.app_activa = False

    def iniciar_captura(self):
        audio_q = queue.Queue()

        def sd_callback(indata, frames, time_info, status):
            audio_q.put(bytes(indata))

        stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=VAD_FRAME_SAMPLES,
            dtype='int16',
            channels=1,
            callback=sd_callback,
        )

        buffer_habla = bytearray()
        en_habla = False
        tiempo_inicio_habla = None

        print(f"🎤 [MICRÓFONO LISTO - VAD] Di '{NOMBRE_ROBOT}' seguido de un comando...")

        with stream:
            while self.app_activa:
                try:
                    chunk_bytes = audio_q.get(timeout=0.5)
                except queue.Empty:
                    continue

                chunk_np = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                chunk_tensor = torch.from_numpy(chunk_np)

                evento = self.vad_iterator(chunk_tensor, return_seconds=False)

                if evento and 'start' in evento and not en_habla:
                    en_habla = True
                    buffer_habla = bytearray()
                    tiempo_inicio_habla = time.time()

                if en_habla:
                    buffer_habla.extend(chunk_bytes)

                corte_por_duracion = (
                    en_habla and tiempo_inicio_habla is not None
                    and (time.time() - tiempo_inicio_habla) >= MAX_DURACION_SEGMENTO_SEG
                )

                if (evento and 'end' in evento and en_habla) or corte_por_duracion:
                    en_habla = False
                    self.vad_iterator.reset_states()
                    if corte_por_duracion:
                        print(f"⏱️ [VAD] Corte forzado tras {MAX_DURACION_SEGMENTO_SEG:.0f}s")
                    
                    if len(buffer_habla) >= int(SAMPLE_RATE * 0.3) * 2:
                        self.segmentos_pendientes.put((bytes(buffer_habla), time.time()))
                    buffer_habla = bytearray()
                    tiempo_inicio_habla = None
