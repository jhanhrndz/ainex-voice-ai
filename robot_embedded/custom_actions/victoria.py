#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Victoria.
El robot levanta ambos brazos en forma de V triunfal y mira un poco hacia arriba.
Ubicación: src/custom_actions/victoria.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Levantar brazos en forma de V y mirar arriba
    # Brazo Derecho:
    setBusServoPulse(14, 850, 1000)  # Hombro pitch arriba (recto vertical)
    setBusServoPulse(16, 300, 1000)  # Hombro roll abriendo hacia afuera
    setBusServoPulse(18, 500, 1000)  # Codo recto
    
    # Brazo Izquierdo:
    setBusServoPulse(13, 150, 1000)  # Hombro pitch arriba (recto vertical)
    setBusServoPulse(15, 700, 1000)  # Hombro roll abriendo hacia afuera
    setBusServoPulse(17, 500, 1000)  # Codo recto
    
    # Cabeza mirando arriba (tilt up)
    if setServoPulse:
        setServoPulse(24, 630, 1000)
    
    sleep(1.0)
    
    # Pequeño festejo moviendo los hombros (roll) rápidamente adentro y afuera
    for _ in range(3):
        setBusServoPulse(16, 250, 200)
        setBusServoPulse(15, 750, 200)
        sleep(0.2)
        setBusServoPulse(16, 300, 200)
        setBusServoPulse(15, 700, 200)
        sleep(0.2)
    
    sleep(1.0) # Mantiene la V un momento más

    # 2. Bajar a posición de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    
    setBusServoPulse(13, 835, 1000)
    setBusServoPulse(15, 830, 1000)
    
    if setServoPulse:
        setServoPulse(24, 500, 1000) # Cabeza centrada

    sleep(1.2)
    gait_manager.enable()
