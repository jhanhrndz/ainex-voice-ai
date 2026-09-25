import requests
import random
from config.settings import OLLAMA_URL, MODEL_NAME

class OllamaClient:
    def __init__(self):
        self.url = OLLAMA_URL
        self.model = MODEL_NAME

    def precalentar_modelo(self):
        """Envía una imagen negra 1x1 en base64 para cargar el modelo en VRAM."""
        print(f"🔥 Pre-calentando modelo {self.model}...")
        pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY3jP4PgfAAWpA61iN1YmAAAAAElFTkSuQmCC"
        payload = {
            "model": self.model,
            "prompt": "describe",
            "images": [pixel_b64],
            "stream": False
        }
        try:
            requests.post(self.url, json=payload, timeout=20)
            print(f"✅ {self.model} cargado y listo.\n")
        except Exception:
            print(f"⚠️ No se pudo pre-calentar {self.model}. El primer escaneo tardará más.\n")

    def consultar(self, prompt, imagen_base64, temperature=0.0, num_predict=10, stop=None):
        if stop is None:
            stop = ["\n", "."]
            
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [imagen_base64] if imagen_base64 else [],
            "stream": False,
            "keep_alive": "30s",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "stop": stop
            }
        }
        try:
            response = requests.post(self.url, json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            print(f"⚠️ Ollama respondió código {response.status_code}: {response.text[:200]}")
            return "error"
        except requests.exceptions.Timeout:
            print(f"⚠️ {self.model} tardó más de 45s. ¿Está cargado el modelo?")
            return "error"
        except requests.exceptions.ConnectionError:
            print("⚠️ No se pudo conectar a Ollama. ¿Está encendido?")
            return "error"
        except Exception as e:
            print(f"⚠️ Error inesperado consultando Ollama: {e}")
            return "error"

    def preguntar_direccion(self, imagen_base64):
        prompt = (
            "This image is a panoramic view divided into three sections: Left, Center, and Right. "
            "Look at the floor. Find the section that has the widest, deepest, and clearest open floor space "
            "to walk safely without hitting any obstacles. "
            "Answer ONLY with one word: left, center, or right."
        )
        try:
            print(f"🧠 Analizando entorno con {self.model}...")
            # Perfil estricto: 0.0 temp, max 10 tokens, cortar rápido
            respuesta = self.consultar(
                prompt, 
                imagen_base64, 
                temperature=0.0, 
                num_predict=10, 
                stop=["\n", "."]
            ).lower()
            
            print(f"🧠 [Visión IA]: \"{respuesta}\"")
            
            if respuesta == "error" or not respuesta:
                return "error"
                
            for c in [".", ",", '"', "'", "\n", "`"]:
                respuesta = respuesta.replace(c, "")
                
            if "center" in respuesta or "forward" in respuesta:
                return "adelante"
            elif "left" in respuesta:
                return "izquierda"
            elif "right" in respuesta:
                return "derecha"
            elif "back" in respuesta or "backward" in respuesta:
                return "atras"
                
            return random.choice(["izquierda", "derecha"]) # Fail-safe
        except Exception:
            return "error"

    def identificar_persona(self, imagen_base64):
        prompt = (
            "What do you see in front of the robot? Describe the scene in natural Spanish in one short sentence. "
            "Do not output coordinates, boxes or numbers."
        )
        try:
            print(f"🧠 Describiendo escena con {self.model}...")
            # Perfil descriptivo: mayor temperatura para naturalidad, más tokens, sin paradas abruptas
            desc = self.consultar(
                prompt, 
                imagen_base64, 
                temperature=0.3, 
                num_predict=80, 
                stop=[]
            )
            
            if desc.startswith("[") and desc.endswith("]"):
                desc = "Veo el camino frente a mí con objetos en el entorno."
            return desc
        except Exception:
            return "error"
