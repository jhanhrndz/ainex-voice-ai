#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimiento personalizado: Gesto de Duda / No lo sé (Encogerse de hombros con brazos abiertos).
Ubicación: src/custom_actions/duda.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # 1. Abrir ambos antebrazos a los lados con palmas arriba
    setBusServoPulse(14, 380, 800)
    setBusServoPulse(16, 320, 800)
    setBusServoPulse(18, 650, 800)
    setBusServoPulse(20, 800, 800)

    setBusServoPulse(13, 620, 800)
    setBusServoPulse(15, 680, 800)
    setBusServoPulse(17, 350, 800)
    setBusServoPulse(19, 200, 800)

    # Ladear cabeza a los lados
    if setServoPulse:
        setServoPulse(23, 420, 500)
        sleep(0.7)
        setServoPulse(23, 580, 500)
        sleep(0.7)
        setServoPulse(23, 500, 400)
        sleep(0.8)
    else:
        sleep(2.2)

    # 2. Regreso suave a reposo
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
