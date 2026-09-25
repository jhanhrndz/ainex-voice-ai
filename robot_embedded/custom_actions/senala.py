#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Señalar (Apuntar al frente).
El robot levanta su brazo derecho de forma totalmente horizontal y apuntando al frente,
sin levantarlo hacia el cielo.
Ubicación: src/custom_actions/senala.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Apuntar con el brazo derecho horizontal al frente
    # Pitch (14) en ~500 es totalmente horizontal.
    # Roll (16) en 170 es paralelo al cuerpo, apuntando al frente exacto.
    # Codo (18) en 500 es totalmente recto.
    setBusServoPulse(14, 500, 800)
    setBusServoPulse(16, 170, 800)
    setBusServoPulse(18, 500, 800)
    
    # Mantener el izquierdo abajo (reposo)
    setBusServoPulse(13, 835, 800)
    setBusServoPulse(15, 830, 800)
    setBusServoPulse(17, 500, 800)

    # Si hay control de cabeza, miramos un poco hacia el frente/abajo y centrado
    if setServoPulse:
        setServoPulse(23, 500, 800)
        setServoPulse(24, 450, 800)
        
    sleep(0.8) # Espera a llegar a la posición
    
    # Mantener postura de señalar
    sleep(2.0)

    # 2. Descender suavemente a postura base de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    
    if setServoPulse:
        setServoPulse(24, 500, 1000) # Restaurar cabeza
        
    sleep(1.2)
    gait_manager.enable()
