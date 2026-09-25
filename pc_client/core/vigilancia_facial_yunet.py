import os
import time
import cv2

CARPETA_VIGILANCIA = os.path.join("capturas", "vigilancia")
os.makedirs(CARPETA_VIGILANCIA, exist_ok=True)

# Ruta del modelo YuNet
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_YUNET = os.path.join(DIRECTORIO_ACTUAL, "..", "models", "face_detection_yunet_2023mar.onnx")

# Inicializacion del detector YuNet una sola vez al cargar el modulo
detector_yunet = None
try:
    if os.path.exists(RUTA_YUNET):
        detector_yunet = cv2.FaceDetectorYN.create(
            model=RUTA_YUNET,
            config="",
            input_size=(640, 480),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5
        )
        print("[INFO] OpenCV YuNet inicializado correctamente para vigilancia facial.")
    else:
        print(f"[ALERTA] Modelo YuNet no encontrado en: {RUTA_YUNET}")
except Exception as e_yunet:
    print(f"[ERROR] No se pudo inicializar YuNet: {e_yunet}")


def detectar_rostro_en_imagen(ruta_imagen):
    """
    Detecta si existe al menos un rostro en la imagen usando YuNet.
    Retorna: (hay_rostro: bool, num_rostros: int, tiempo_ms: float)
    """
    global detector_yunet
    if detector_yunet is None or not os.path.exists(ruta_imagen):
        return False, 0, 0.0

    img = cv2.imread(ruta_imagen)
    if img is None:
        return False, 0, 0.0

    h, w, _ = img.shape
    detector_yunet.setInputSize((w, h))

    t_inicio = time.perf_counter()
    _, caras = detector_yunet.detect(img)
    t_ms = (time.perf_counter() - t_inicio) * 1000.0

    if caras is not None and len(caras) > 0:
        # Dibujar cuadro delimitador verde para depuracion visual
        for cara in caras:
            box = list(map(int, cara[:4]))
            confianza = cara[-1]
            cv2.rectangle(img, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), (0, 255, 0), 2)
            cv2.putText(
                img,
                f"Cara: {confianza:.2f}",
                (box[0], max(20, box[1] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        # Guardar imagen con anotaciones
        cv2.imwrite(ruta_imagen, img)
        return True, len(caras), t_ms

    return False, 0, t_ms


def ejecutar_ronda_vigilancia_yunet(controlador, funcion_tomar_foto, funcion_saludar):
    """
    Escaneo frame a frame ultrarrapido con OpenCV YuNet (<15 ms de inferencia).
    Evalua las 3 posiciones (izquierda, centro, derecha).
    Si detecta un rostro en alguna, acciona el saludo.
    """
    posiciones = ['izquierda', 'centro', 'derecha']
    print('\n[REPOSO] Iniciando patrullaje facial con OpenCV YuNet...')

    try:
        # Levantar la cabeza para buscar rostros
        controlador.inclinar_camara('arriba')

        for pos in posiciones:
            print(f'Mirando a la {pos}...')
            controlador.mover_camara(pos)
            nombre_temp = os.path.join(CARPETA_VIGILANCIA, f'vigilancia_{pos}.jpg')
            ruta = funcion_tomar_foto(nombre_temp)

            if ruta:
                hay_rostro, num_caras, ms = detectar_rostro_en_imagen(ruta)
                print(f"[YUNET]: {ms:.2f} ms | Rostros detectados: {num_caras}")

                if hay_rostro:
                    print(f'Rostro detectado por YuNet en la posicion: {pos}! Saludando...')
                    funcion_saludar()
                else:
                    print(f'    (Sin rostros en la {pos})')

    except Exception as e:
        print(f'[ERROR] Fallo en la ronda de vigilancia YuNet: {e}')

    finally:
        # Bajar la cabeza a la posicion neutra y centrar
        controlador.inclinar_camara('frente')
        controlador.mover_camara('centro')

    return None
