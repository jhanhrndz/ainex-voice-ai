#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Aplauso (Clapping).
Doble los codos fuertemente frente al pecho para aplaudir y no con los brazos extendidos.
Ubicación: src/custom_actions/aplauso.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Llevar ambos brazos al frente y flexionar los codos frente al pecho
    # Pitch (14, 13) llevados al frente (~500)
    # Codos (18, 17) doblados al máximo hacia el pecho (260 Der, 740 Izq)
    setBusServoPulse(14, 500, 800)
    setBusServoPulse(18, 260, 800)
    
    setBusServoPulse(13, 500, 800)
    setBusServoPulse(17, 740, 800)
    
    # Abrir los brazos (preparar aplauso) moviendo los hombros (Roll)
    setBusServoPulse(16, 260, 800) # Derecha abierta
    setBusServoPulse(15, 740, 800) # Izquierda abierta
    
    sleep(0.8)

    # 2. Secuencia de aplausos rápidos usando los hombros Roll (16, 15)
    for _ in range(4):
        # Cerrar rápido (impacto / aplauso)
        setBusServoPulse(16, 190, 150)
        setBusServoPulse(15, 810, 150)
        sleep(0.15)
        # Abrir rápido
        setBusServoPulse(16, 250, 150)
        setBusServoPulse(15, 750, 150)
        sleep(0.15)

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