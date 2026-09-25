import re
import unicodedata
from rapidfuzz import fuzz, process
from config.settings import NOMBRE_ROBOT, WAKE_WORD_THRESHOLD, INTENT_THRESHOLD, AMBIGUEDAD_MARGEN, PARAR_THRESHOLD
from config.intents import CANONICOS

class NLPEngine:
    def __init__(self):
        self.nombre_robot_norm = self.normalizar_texto(NOMBRE_ROBOT)
        self.corpus = [(self.normalizar_texto(frase), intent_id) for intent_id, frases in CANONICOS.items() for frase in frases]
        self.frases = [f for f, _ in self.corpus]

    @staticmethod
    def normalizar_texto(texto):
        """Minúsculas, sin tildes, sin puntuación, espacios colapsados."""
        texto = texto.lower().strip()
        texto = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto

    def contiene_wake_word(self, texto_norm):
        """Detecta el wake word por similitud, sin depender de una lista de variantes fija."""
        for palabra in texto_norm.split():
            if fuzz.ratio(palabra, self.nombre_robot_norm) >= WAKE_WORD_THRESHOLD:
                return True, palabra
        return False, None

    def quitar_wake_word(self, texto_norm, palabra_detectada):
        palabras = texto_norm.split()
        if palabra_detectada in palabras:
            palabras.remove(palabra_detectada)
        return ' '.join(palabras).strip()

    def clasificar_intencion(self, texto_norm):
        """Devuelve (intent_id, score, es_ambiguo). intent_id es None si no hay match aceptable."""
        if not texto_norm:
            return None, 0, False

        resultados = process.extract(texto_norm, self.frases, scorer=fuzz.WRatio, limit=2)
        if not resultados:
            return None, 0, False

        _, mejor_score, mejor_idx = resultados[0]
        mejor_intent = self.corpus[mejor_idx][1]

        if mejor_score < INTENT_THRESHOLD:
            return None, mejor_score, False

        if len(resultados) > 1:
            _, segundo_score, segundo_idx = resultados[1]
            segundo_intent = self.corpus[segundo_idx][1]
            if segundo_intent != mejor_intent and (mejor_score - segundo_score) < AMBIGUEDAD_MARGEN:
                return mejor_intent, mejor_score, True

        return mejor_intent, mejor_score, False

    def es_orden_de_parar(self, texto_norm):
        """Chequeo de seguridad con fuzz.ratio estricto."""
        if not texto_norm:
            return False
        mejor = process.extractOne(texto_norm, CANONICOS["parar"], scorer=fuzz.ratio)
        return bool(mejor and mejor[1] >= PARAR_THRESHOLD)
