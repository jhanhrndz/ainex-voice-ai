# 🦾 Cinemática, Hardware y Mapeo Articular del AiNex

Este documento proporciona la especificación técnica de hardware, distribución de grados de libertad (DOF), mapeo de servomotores serie y guía cinemática para la creación de acciones dinámicas en el robot humanoide **Hiwonder AiNex**.

---

## 1. Especificaciones Físicas y de Hardware

- **Plataforma:** Hiwonder AiNex Humanoid Robot.
- **Grados de Libertad Totales:** 24 servomotores inteligentes de bus serie.
  - **Cabeza / Cuello:** 2 DOF (Pan, Tilt).
  - **Brazos y Hombros:** 8 DOF (4 por brazo: Hombro Pitch, Hombro Roll, Codo Pitch, Muñeca Yaw).
  - **Piernas y Cadera:** 12 DOF (6 por pierna: Cadera Yaw, Cadera Roll, Cadera Pitch, Rodilla Pitch, Tobillo Pitch, Tobillo Roll).
  - **Manos:** 2 DOF (Apertura/Cierre o fijas según variante).
- **Controlador Embebido:** Placa controladora de servos serie conectada por bus UART (`/dev/ttyAMA0`) a una Raspberry Pi 4B (Ubuntu 20.04 LTS + ROS Noetic).
- **Rango de Pulso Operativo:** `0` a `1000` (pulso neutro / centro en `500`).

---

## 2. Tabla de Mapeo de Servomotores (Tren Superior y Cabeza)

El siguiente mapa articular fue obtenido mediante ingeniería inversa del archivo maestro de configuración `hiwonder_servo_controller.yaml`:

| Articulación | ID Servo | Pulso Reposo | Rango Físico | Dirección del Movimiento |
|---|:---:|:---:|:---:|---|
| **Cabeza - Pan (Giro H)** | `23` | `500` | 250 - 750 | Menor: Giro a la Derecha \| Mayor: Giro a la Izquierda |
| **Cabeza - Tilt (Inclinación V)**| `24` | `500` | 300 - 630 | Menor: Mirar Abajo (suelo) \| Mayor: Mirar Arriba (cielo) |
| **Hombro Derecho - Pitch** | `14` | `165` (abajo) | 125 - 850 | `125`: Reposo abajo \| `500`: Horizontal al frente \| `850`: Vertical arriba |
| **Hombro Derecho - Roll** | `16` | `170` (pegado) | 150 - 350 | `170`: Alineado paralelo \| `250+`: Apertura lateral hacia afuera |
| **Codo Derecho - Pitch** | `18` | `500` (recto) | 220 - 550 | `500`: Brazo totalmente extendido \| `240 - 260`: Flexión máxima (pecho/mentón) |
| **Muñeca Derecha - Yaw** | `20` | `930` (neutro) | 700 - 1000 | Rotación de antebrazo / orientación de palma |
| **Hombro Izquierdo - Pitch** | `13` | `835` (abajo) | 150 - 875 | `835`: Reposo abajo \| `500`: Horizontal al frente \| `150`: Vertical arriba |
| **Hombro Izquierdo - Roll** | `15` | `830` (pegado) | 650 - 850 | `830`: Alineado paralelo \| `750-`: Apertura lateral hacia afuera |
| **Codo Izquierdo - Pitch** | `17` | `500` (recto) | 450 - 780 | `500`: Brazo totalmente extendido \| `740 - 760`: Flexión máxima (pecho/mentón) |
| **Muñeca Izquierda - Yaw** | `19` | `70` (neutro) | 0 - 300 | Rotación de antebrazo / orientación de palma |

---

## 3. Principio de Simetría en Espejo (Mirror Symmetry)

> [!IMPORTANT]
> Los servomotores de las extremidades izquierda y derecha están montados físicamente en **orientación invertida (espejo)** para mantener el balance y el centro de gravedad.

Esto genera una regla matemática fundamental al diseñar movimientos en código:

1. **Hombro Pitch (Elevación Frontal):**
   - Subir brazo derecho (ID 14): Requiere **aumentar** el valor del pulso (`165 ➔ 500 ➔ 850`).
   - Subir brazo izquierdo (ID 13): Requiere **disminuir** el valor del pulso (`835 ➔ 500 ➔ 150`).
2. **Hombro Roll (Apertura Lateral / Separación):**
   - Abrir brazo derecho hacia afuera (ID 16): Requiere **aumentar** el pulso (`170 ➔ 250`).
   - Abrir brazo izquierdo hacia afuera (ID 15): Requiere **disminuir** el pulso (`830 ➔ 750`).
3. **Codo Pitch (Flexión Articular):**
   - Doblar codo derecho (ID 18): Requiere valores **bajos** (`500 ➔ 260`).
   - Doblar codo izquierdo (ID 17): Requiere valores **altos** (`500 ➔ 740`).

---

## 4. Control de Concurrencia Cinemática: GaitManager

El robot ejecuta en segundo plano un nodo de cinemática inversa (`GaitManager`) que estabiliza las piernas y los brazos durante el ciclo de marcha.

Si un script de Python intenta enviar pulsos manuales a los servos mientras `GaitManager` está activo, **se produce una colisión de buses UART**, provocando que el robot tiemble violentamente o se dañen los engranajes metálicos.

Por esta razón, cada movimiento personalizado **debe respetar estrictamente este protocolo**:

```python
def run(gait_manager, setBusServoPulse, setServoPulse=None):
    # 1. Detener marcha y desactivar motor de cinemática inversa
    gait_manager.stop()
    gait_manager.disable()

    try:
        # 2. Ejecutar secuencias articulares manuales
        setBusServoPulse(14, 500, 800) # servo_id, pulso, duracion_ms
        # ...
        sleep(1.0)
    finally:
        # 3. Devolver siempre el control al motor cinemático oficial
        gait_manager.enable()
```

---

## 5. Guía de Creación de una Acción Personalizada (*Custom Action*)

Para agregar un nuevo movimiento al robot, sigue estos pasos:

1. Crea un archivo `.py` dentro de `robot_embedded/custom_actions/` con el nombre exacto de la intención (ej: `patada_ninja.py`).
2. Implementa la función `run(gait_manager, setBusServoPulse, setServoPulse=None)`.
3. Establece tiempos de interpolación adecuados en milisegundos (`duration_ms` en `setBusServoPulse`) y añade `sleep()` para permitir que la inercia física del robot complete la trayectoria antes de enviar el siguiente pulso.
4. Finaliza siempre devolviendo los miembros a la postura base de reposo antes de llamar a `gait_manager.enable()`.

### Plantilla de Código Estándar

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acción Personalizada: Saludo con la Mano Derecha
Ubicación: robot_embedded/custom_actions/mi_accion.py
"""
from time import sleep

def run(gait_manager, setBusServoPulse, setServoPulse=None):
    gait_manager.stop()
    gait_manager.disable()

    # Fase 1: Elevar brazo derecho al frente
    setBusServoPulse(14, 550, 800) # Hombro Pitch
    setBusServoPulse(16, 220, 800) # Hombro Roll (separación segura)
    setBusServoPulse(18, 280, 800) # Codo flexionado
    sleep(1.0)

    # Fase 2: Retorno suave a reposo
    setBusServoPulse(14, 165, 1000)
    setBusServoPulse(16, 170, 1000)
    setBusServoPulse(18, 500, 1000)
    sleep(1.2)

    gait_manager.enable()
```
