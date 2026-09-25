#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Reverencia (Bow).
Cruza los brazos sobre el pecho y baja la cabeza para simular una reverencia profunda.
Ubicación: src/custom_actions/reverencia.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Cruzar brazos sobre el pecho
    # Brazo derecho flexionado y pegado
    setBusServoPulse(14, 450, 1000)
    setBusServoPulse(16, 150, 1000) # Roll hacia adentro
    setBusServoPulse(18, 250, 1000) # Codo fuertemente flexionado
    
    # Brazo izquierdo flexionado y pegado
    setBusServoPulse(13, 550, 1000)
    setBusServoPulse(15, 850, 1000) # Roll hacia adentro
    setBusServoPulse(17, 750, 1000) # Codo fuertemente flexionado

    # Cabeza fuertemente hacia abajo simulando la reverencia
    if setServoPulse:
        setServoPulse(24, 300, 1000) # Tilt abajo máximo seguro
        
    sleep(1.0)
    
    # Mantener reverencia
    sleep(2.0)

    # 2. Descender suavemente a postura base de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    setBusServoPulse(18, 500, 1000)
    
    setBusServoPulse(13, 835, 1000)
    setBusServoPulse(15, 830, 1000)
    setBusServoPulse(17, 500, 1000)
    
    if setServoPulse:
        setServoPulse(24, 500, 1000) # Restaurar cabeza
        
    sleep(1.2)
    gait_manager.enable()
