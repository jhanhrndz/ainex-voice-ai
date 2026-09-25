#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Meme 67.
Un baile rítmico alternando los brazos arriba y abajo al estilo del meme de internet "el paso del 67".
No mueve la cabeza.
Ubicación: src/custom_actions/meme_67.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Posición inicial: Brazos al frente y codos flexionados
    setBusServoPulse(14, 500, 800)
    setBusServoPulse(16, 250, 800) # Mayor separación lateral (antes 200) para no chocar
    setBusServoPulse(18, 300, 800) # Codo der flexionado
    
    setBusServoPulse(13, 500, 800)
    setBusServoPulse(15, 750, 800) # Mayor separación lateral (antes 800) para no chocar
    setBusServoPulse(17, 700, 800) # Codo izq flexionado
    
    sleep(0.8)

    # 2. Secuencia rítmica del "67" (Alternando)
    # Como los motores están montados en espejo:
    # Para 14 (Der): 650 es arriba, 350 es abajo.
    # Para 13 (Izq): 650 es abajo, 350 es arriba.
    for _ in range(4):
        # Beat A: Brazo Derecho ARRIBA (650), Brazo Izquierdo ABAJO (650)
        setBusServoPulse(14, 650, 400)
        setBusServoPulse(13, 650, 400)
        sleep(0.4)
        
        # Beat B: Brazo Derecho ABAJO (350), Brazo Izquierdo ARRIBA (350)
        setBusServoPulse(14, 350, 400)
        setBusServoPulse(13, 350, 400)
        sleep(0.4)

    # Pausa al final de la pose rítmica para que termine limpio
    sleep(0.5)

    # 3. Regresar a posición de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    setBusServoPulse(18, 500, 1000)
    
    setBusServoPulse(13, 835, 1000)
    setBusServoPulse(15, 830, 1000)
    setBusServoPulse(17, 500, 1000)
    
    sleep(1.2)
    gait_manager.enable()
