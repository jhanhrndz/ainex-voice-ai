import os
import time

CARPETA_VIGILANCIA = os.path.join("capturas", "vigilancia")
os.makedirs(CARPETA_VIGILANCIA, exist_ok=True)

def ejecutar_ronda_vigilancia(controlador, funcion_tomar_foto, funcion_b64, funcion_ia, funcion_saludar):
    """
    Escaneo frame a frame usando el modelo VLM.
    Evalúa las 3 posiciones obligatoriamente. Si detecta un rostro en alguna, acciona el saludo.
    """
    posiciones = ['izquierda', 'centro', 'derecha']
    print('\n💤 [REPOSO] Iniciando patrullaje facial (buscando rostros)...')
    
    prompt = "Look carefully at the image. Is there a human face clearly visible? Answer ONLY yes or no."
    
    try:
        # Levantar la cabeza para buscar rostros
        controlador.inclinar_camara('arriba')
        
        for pos in posiciones:
            print(f'👀 Mirando a la {pos}...')
            controlador.mover_camara(pos)
            nombre_temp = os.path.join(CARPETA_VIGILANCIA, f'vigilancia_{pos}.jpg')
            ruta = funcion_tomar_foto(nombre_temp)
            
            if ruta:
                img_b64 = funcion_b64(ruta)
                respuesta = funcion_ia(prompt, img_b64).lower()

                print(f"[RESPUESTA MODELO]: {respuesta}")
                
                # Limpiamos puntuación por si la IA añade un punto
                respuesta = respuesta.replace(".", "").strip()
                
                if "yes" in respuesta:
                    print(f'👤 ¡Rostro detectado por IA en la posición: {pos}! Saludando...')
                    # Ejecuta el saludo y pausa el escaneo temporalmente mientras saluda
                    funcion_saludar()
                else:
                    print(f'    (Sin rostros en la {pos})')
                
    except Exception as e:
        print(f'[ERROR] Fallo en la ronda de vigilancia: {e}')
        
    finally:
        # Bajar la cabeza a la posición neutra y centrar
        controlador.inclinar_camara('frente')
        controlador.mover_camara('centro')
        
    return None
