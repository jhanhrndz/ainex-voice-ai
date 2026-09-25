# Movimientos Personalizados - AiNex

Esta carpeta almacena los scripts en Python para las poses y acciones dinámicas del robot AiNex, orquestados desde el cliente de socket.

## Reglas para crear un movimiento:
1. El archivo debe nombrarse exactamente igual al intento mapeado (ej: `guardia.py`).
2. Debe contener una función `run(gait_manager, setBusServoPulse, setServoPulse=None)`.
3. Es **obligatorio** llamar a `gait_manager.disable()` al inicio y `gait_manager.enable()` al final para evitar conflicto con la cinemática inversa.
4. Tiempos de espera: Usa `time.sleep()` entre movimientos para dar tiempo físico a los motores de llegar a la posición dictada.

## Lista actual:
- `guardia.py`
- `levanta_mano.py`
- `victoria.py`
- `senala.py`
- `aplauso.py`
- `pensativo.py`
- `reverencia.py`
- `duda.py`
- `meme_67.py`
