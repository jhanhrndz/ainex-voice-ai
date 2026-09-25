import cv2
import os
import time
import base64
from config.settings import DIR_IP

class RobotVision:
    def __init__(self, controlador):
        self.controlador = controlador

    def tomar_foto(self, nombre_archivo):
        url = f"http://{DIR_IP}:8080/stream?topic=/camera/image_raw"
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                return None
            time.sleep(0.8)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                cv2.imwrite(nombre_archivo, frame)
                return nombre_archivo
            return None
        except Exception:
            return None

    def capturar_tres_fotos(self, detener_evento):
        frames = []
        posiciones = ['izquierda', 'centro', 'derecha']
        carpeta_exploracion = os.path.join("capturas", "exploracion")
        os.makedirs(carpeta_exploracion, exist_ok=True)
        
        try:
            for i, pos in enumerate(posiciones):
                if detener_evento.is_set():
                    return None
                self.controlador.mover_camara(pos)
                nombre = os.path.join(carpeta_exploracion, f"imagen_{i+1}.jpg")
                
                ruta = self.tomar_foto(nombre)
                if not ruta:
                    print(f"⚠️ Fallo al capturar {pos}. Reintentando en 0.5s...")
                    time.sleep(0.5)
                    ruta = self.tomar_foto(nombre)
                    
                if ruta:
                    img = cv2.imread(ruta)
                    if img is not None:
                        img_resized = cv2.resize(img, (320, 240))
                        frames.append(img_resized)
                    time.sleep(0.2)
                else:
                    print(f"❌ Abortando escaneo: Imposible capturar vista {pos}.")
                    return None

            if len(frames) == 3 and not detener_evento.is_set():
                panorama = cv2.hconcat(frames)
                panorama_gris = cv2.cvtColor(panorama, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
                panorama_filtrado = clahe.apply(panorama_gris)
                panorama_3c = cv2.cvtColor(panorama_filtrado, cv2.COLOR_GRAY2BGR)
                
                alto, ancho = panorama_3c.shape[:2]
                delta_h = ancho - alto
                top, bottom = delta_h // 2, delta_h - (delta_h // 2)
                
                cuadrado = cv2.copyMakeBorder(panorama_3c, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                
                panorama_path = os.path.join(carpeta_exploracion, "panorama.jpg")
                cv2.imwrite(panorama_path, cuadrado)
                return panorama_path
            return None
            
        finally:
            self.controlador.mover_camara('centro')
            for i in range(1, 4):
                temp_img = os.path.join(carpeta_exploracion, f"imagen_{i}.jpg")
                if os.path.exists(temp_img):
                    try:
                        os.remove(temp_img)
                    except Exception:
                        pass

    @staticmethod
    def convertir_imagen_a_base64(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
