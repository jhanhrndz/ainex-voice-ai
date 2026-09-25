#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Levantar la mano.
Usa exactamente Frame 1 para subir y Frame 8 para bajar de greet.d6a oficial.
Ubicación: src/custom_actions/levanta_mano.py
"""

from time import sleep

def run(gait_manager, setBusServoPulse):
    """
    Sube a la postura de saludo oficial (Frame 1 de greet.d6a),
    la sostiene quieta durante 3 segundos, y luego baja a la postura
    exacta de reposo oficial (Frame 8 de greet.d6a).
    """
    # 1. Asegurar estabilidad cinemática
    gait_manager.stop()
    gait_manager.disable()

    # 2. Subir a la postura exacta de saludo oficial (Frame 1 de greet.d6a)
    setBusServoPulse(14, 600, 1000)  # Hombro pitch
    setBusServoPulse(16, 500, 1000)  # Hombro roll
    setBusServoPulse(18, 500, 1000)  # Codo pitch
    setBusServoPulse(20, 800, 1000)  # Muñeca / antebrazo yaw
    sleep(3.0)                       # Sostener en alto

    # 3. Descender a la postura exacta de reposo oficial (Frame 8 de greet.d6a)
    setBusServoPulse(14, 165, 1000)  # Hombro reposo
    setBusServoPulse(16, 170, 1000)  # Hombro lateral pegado al cuerpo
    setBusServoPulse(18, 500, 1000)  # Codo neutro
    setBusServoPulse(20, 930, 1000)  # Muñeca orientación neutra de reposo
    sleep(1.2)

    # 4. Reactivar marcha
    gait_manager.enable()
