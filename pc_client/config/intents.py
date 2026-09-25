# =========================================================
# CANÓNICOS DE COMANDOS — cada intención con sus frases de ejemplo
# =========================================================
CANONICOS = {
    "saluda":       ["saluda", "saludo", "hola", "saludar"],
    "baila_twist":  ["muevete", "twist", "menea"],
    "pase_robot":   ["baila", "baile", "pase del robot", "pase robot"],
    "patea":        ["patear", "patea", "patada", "chuta"],
    "firmes":       ["firmes", "firme", "parate", "posicion firme"],
    "listo":        ["listo", "preparado", "posicion caminar"],
    "levantate":    ["levantate", "recuperate", "ponte de pie"], # Boca abajo a pararse
    "parate":       ["parate", "puente"], # Boca arriba a pararse
    "brazos_atras": ["brazos atras", "guarda brazos", "recoge brazos"],
    "levanta_mano": ["levanta la mano", "mano derecha", "levanta tu mano", "pide la palabra", "alza la mano", "pregunta"],
    "victoria":     ["victoria", "celebra", "ganamos", "campeon", "festeja"],
    "senala":       ["senala", "apunta", "mira alla", "alla"],
    "aplauso":      ["aplaude", "aplauso", "aplausos", "bravo"],
    "guardia":      ["en guardia", "guardia", "a pelear", "pelea", "boxea"],
    "pensativo":    ["piensa", "pensativo", "reflexiona"],
    "reverencia":   ["reverencia", "agradece", "respeto", "inclinacion"],
    "duda":         ["no se", "duda", "quien sabe", "dudoso"],
    "meme_67":      ["67", "six seven", "meme sesenta y siete", "el sesenta y siete", "aura", "meme 67", "laura"],
    "explora":      ["explora", "navega", "camina solo", "busca camino", "modo exploracion"],
    "describe":     ["describe", "que ves", "quien esta ahi", "mira", "que hay"],
    "adelante":     ["adelante", "avanza", "camina adelante"],
    "atras":        ["atras", "retrocede", "camina atras"],
    "izquierda":    ["gira izquierda", "izquierda"],
    "derecha":      ["gira derecha", "derecha"],
    "parar":        ["para", "detente", "stop", "alto", "quieto", "espera"],
}

# Mapeo de intención -> comando literal enviado por socket al robot
COMANDO_SOCKET = {
    "saluda": "greet",
    "baila_twist": "twist",
    "pase_robot": "wave",
    "patea": "right_shot",
    "firmes": "stand",
    "listo": "walk_ready",
    "levantate": "lie_to_stand",
    "parate": "recline_to_stand",
    "brazos_atras": "hand_back",
    "levanta_mano": "levanta_mano",
    "victoria": "victoria",
    "senala": "senala",
    "aplauso": "aplauso",
    "guardia": "guardia",
    "pensativo": "pensativo",
    "reverencia": "reverencia",
    "duda": "duda",
    "meme_67": "meme_67",
    "adelante": "adelante",
    "atras": "atras",
    "izquierda": "izquierda",
    "derecha": "derecha",
    "parar": "parar",
}
