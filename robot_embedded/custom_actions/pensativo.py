#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Pensativo.
Doble el codo fuertemente para llevar la mano derecha hacia el mentón y baja la cabeza.
Ubicación: src/custom_actions/pensativo.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Llevar la mano derecha al mentón
    # El pitch (14) levanta un poco el brazo al frente
    # El codo (18) se flexiona fuertemente para alcanzar la cara (~240)
    # El roll (16) se mantiene cerrado (170-190) para estar cerca del cuerpo
    setBusServoPulse(14, 380, 1000)
    setBusServoPulse(16, 190, 1000)
    setBusServoPulse(18, 240, 1000)
    setBusServoPulse(20, 850, 1000) # Girar muñeca para imitar apoyo en barbilla
    
    # Mantener el izquierdo abajo (reposo)
    setBusServoPulse(13, 835, 1000)
    setBusServoPulse(15, 830, 1000)
    setBusServoPulse(17, 500, 1000)

    # Inclinamos la cabeza hacia abajo y un poco hacia la mano derecha
    if setServoPulse:
        setServoPulse(23, 400, 1000) # Pan (mira a la derecha)
        setServoPulse(24, 400, 1000) # Tilt (mira abajo)
        
    sleep(1.0)
    
    # Quedarse pensando por un tiempo
    sleep(3.0)

    # 2. Descender suavemente a postura base de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    setBusServoPulse(18, 500, 1000)
    setBusServoPulse(20, 930, 1000)
    
    if setServoPulse:
        setServoPulse(23, 500, 1000) # Cabeza centrada
        setServoPulse(24, 500, 1000)
        
    sleep(1.2)
    gait_manager.enable()
