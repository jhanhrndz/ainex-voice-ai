import threading

class TTSEngine:
    def __init__(self):
        # Aquí se podrían cargar otras configuraciones de voz si se desea
        pass

    def speak(self, texto):
        """Reproduce en voz alta el texto en español a través de los altavoces de manera asíncrona."""
        if not texto:
            return

        def _speak():
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(texto)
            except Exception:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.say(texto)
                    engine.runAndWait()
                except Exception:
                    print(f"⚠️ [TTS Error] No se pudo reproducir: {texto}")

        threading.Thread(target=_speak, daemon=True).start()
