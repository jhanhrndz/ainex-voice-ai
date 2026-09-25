#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Posición de Guardia con Separación Paralela.
Mantiene los puños separados a la anchura de los hombros sin chocar entre sí.
Ubicación: src/custom_actions/guardia.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Elevar brazos en guardia manteniendo separación paralela entre manos
    # Hombros roll calibrados para separación justa (~7 cm entre puños): 16: 225, 15: 775
    # Hombros pitch elevados al pecho: 14: 580, 13: 420
    # Codos doblados arriba: 18: 260, 17: 740
    setBusServoPulse(14, 580, 800)  # Sube hombro der al frente
    setBusServoPulse(16, 225, 800)  # Separación paralela (no choca con la izquierda)
    setBusServoPulse(18, 260, 800)  # Codo der doblado arriba
    setBusServoPulse(20, 850, 800)  # Puño der alineado

    setBusServoPulse(13, 420, 800)  # Sube hombro izq al frente
    setBusServoPulse(15, 775, 800)  # Separación paralela (no choca con la derecha)
    setBusServoPulse(17, 740, 800)  # Codo izq doblado arriba
    setBusServoPulse(19, 150, 800)  # Puño izq alineado
    sleep(1.5)  # Mantener guardia paralela limpia

    # 2. Jab derecho (recto al frente en su propio carril)
    setBusServoPulse(14, 600, 250)
    setBusServoPulse(18, 520, 250)  # Estira codo der al frente
    sleep(0.3)
    setBusServoPulse(14, 580, 250)
    setBusServoPulse(18, 260, 250)  # Recoge a guardia separada
    sleep(0.4)

    # 3. Jab izquierdo (recto al frente en su propio carril)
    setBusServoPulse(13, 400, 250)
    setBusServoPulse(17, 480, 250)  # Estira codo izq al frente
    sleep(0.3)
    setBusServoPulse(13, 420, 250)
    setBusServoPulse(17, 740, 250)  # Recoge a guardia separada
    sleep(1.5)  # Mantener guardia final separada

    # 4. Descender suavemente a postura base de reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    setBusServoPulse(18, 500, 1000)
    setBusServoPulse(20, 930, 1000)

    setBusServoPulse(13, 835, 1000)
    setBusServoPulse(15, 830, 1000)
    setBusServoPulse(17, 500, 1000)
    setBusServoPulse(19, 70, 1000)
    sleep(1.2)

    gait_manager.enable()
