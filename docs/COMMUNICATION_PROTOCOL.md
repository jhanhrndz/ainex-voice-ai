# 📡 Especificación del Protocolo de Comunicación y Red

Este documento define la especificación técnica del protocolo de red implementado para la comunicación bidireccional entre la estación de trabajo PC Host y el robot humanoide **AiNex**.

---

## 1. Topología de Red y Arquitectura de Canales

El sistema utiliza dos canales de red independientes sobre el protocolo IP (IPv4):

```mermaid
graph LR
    subgraph PC_Host["PC Host (Estación de Cómputo)"]
        CLI["Socket Client (robot_client.py)"]
        CV["OpenCV VideoCapture (vision.py)"]
    end

    subgraph Robot["Robot AiNex (Raspberry Pi 4B)"]
        SRV["Socket Server: Port 9000 (T800_gait_client.py)"]
        STREAM["Web Video Server: Port 8080 (ROS camera node)"]
    end

    CLI <==|Canal 1: TCP Socket (Comandos bidireccionales)|==> SRV
    CV <---|Canal 2: HTTP/MJPEG (Flujo de video cámara)|--- STREAM
```

- **Canal de Control y Telemetría:** Conexión TCP orientada a conexión en el puerto `9000`.
- **Canal de Visión Computacional:** Flujo HTTP MJPEG en el puerto `8080` transmitiendo el tópico ROS `/camera/image_raw`.

---

## 2. Especificación del Canal de Control (Puerto 9000)

### 2.1. Formato de Trama (Payload Format)
- **Protocolo de Transporte:** TCP (Transmission Control Protocol).
- **Codificación:** UTF-8 / ASCII plano.
- **Delimitador de Fin de Mensaje:** Carácter de salto de línea `\n` (LF - 0x0A).
- **Estructura:**
  ```text
  <COMANDO_STRING>\n
  ```
  *Ejemplo:* `guardia\n`, `adelante\n`, `servo_arriba\n`.

### 2.2. Configuración de TCP Keep-Alive
Para evitar que switches de red, routers Wi-Fi o firewalls cierren silenciosamente sockets inactivos por timeout NAT, se implementó Keep-Alive activo a nivel de kernel:

#### En Windows (PC Host):
Se utiliza la llamada de control de entrada/salida `SIO_KEEPALIVE_VALS`:
```python
nuevo_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
# Sondeo tras 5000 ms de inactividad, con reintentos cada 2000 ms
if hasattr(socket, 'SIO_KEEPALIVE_VALS'):
    nuevo_sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 5000, 2000))
```

#### En Linux (Robot):
Se configuran las banderas `SO_KEEPALIVE`, `TCP_KEEPIDLE` (5s) y `TCP_KEEPINTVL` (2s).

### 2.3. Mecanismo de Reconexión Automática y Tolerancia a Fallos
El cliente en `pc_client/robot/robot_client.py` implementa un envoltorio thread-safe con cerrojo (`threading.Lock`):
- Si ocurre una desconexión accidental (`ConnectionResetError`, `BrokenPipeError` o `OSError`), el cliente captura la excepción inmediatamente.
- Cierra de forma segura el descriptor de archivo residual.
- Ejecuta hasta **3 intentos de reconexión consecutiva** con retardos exponenciales controlados (0.5s, 0.3s) antes de declarar el enlace caído, preservando la continuidad del sistema sin interrumpir la interfaz de voz.

---

## 3. Catálogo de Comandos del Socket

### 3.1. Movimientos de Marcha y Dirección
| Comando | Nivel Despachador | Acción Ejecutada |
|---|:---:|---|
| `adelante\n` | Nivel 1 (Hardware) | Inicia marcha frontal con GaitManager. |
| `atras\n` | Nivel 1 (Hardware) | Inicia retroceso continuo con GaitManager. |
| `izquierda\n` | Nivel 1 (Hardware) | Giro continuo hacia el flanco izquierdo. |
| `derecha\n` | Nivel 1 (Hardware) | Giro continuo hacia el flanco derecho. |
| `parar\n` | Nivel 1 (Hardware) | **Parada de emergencia:** Frena marcha y cancela bucles activos. |

### 3.2. Control de Pan / Tilt de Cuello (Cámara)
| Comando | Nivel Despachador | Acción Ejecutada |
|---|:---:|---|
| `servo_frente\n` | Nivel 1 (Hardware) | Centra la cabeza (Pan: 500, Tilt: 500). |
| `servo_arriba\n` | Nivel 1 (Hardware) | Inclina la cabeza hacia arriba (Tilt: 630) para buscar rostros. |
| `servo_abajo\n` | Nivel 1 (Hardware) | Inclina la cabeza hacia abajo (Tilt: 350) para revisar obstáculos. |
| `servo_izquierda\n` | Nivel 1 (Hardware) | Gira la cabeza 45° a la izquierda (Pan: 680) para barrido panorámico. |
| `servo_derecha\n` | Nivel 1 (Hardware) | Gira la cabeza 45° a la derecha (Pan: 320) para barrido panorámico. |

### 3.3. Acciones Personalizadas (Custom Actions)
| Comando | Nivel Despachador | Archivo Invocado |
|---|:---:|---|
| `guardia\n` | Nivel 2 (Dinámico) | `custom_actions/guardia.py` |
| `victoria\n` | Nivel 2 (Dinámico) | `custom_actions/victoria.py` |
| `senala\n` | Nivel 2 (Dinámico) | `custom_actions/senala.py` |
| `aplauso\n` | Nivel 2 (Dinámico) | `custom_actions/aplauso.py` |
| `pensativo\n` | Nivel 2 (Dinámico) | `custom_actions/pensativo.py` |
| `reverencia\n` | Nivel 2 (Dinámico) | `custom_actions/reverencia.py` |
| `duda\n` | Nivel 2 (Dinámico) | `custom_actions/duda.py` |
| `meme_67\n` | Nivel 2 (Dinámico) | `custom_actions/meme_67.py` |
| `levanta_mano\n`| Nivel 2 (Dinámico) | `custom_actions/levanta_mano.py` |

### 3.4. Cinemáticas de Fábrica (ActionGroups Hiwonder)
| Comando | Nivel Despachador | Archivo Invocado |
|---|:---:|---|
| `greet\n` | Nivel 3 (Oficial) | `ActionGroups/greet.d6a` |
| `twist\n` | Nivel 3 (Oficial) | `ActionGroups/twist.d6a` |
| `wave\n` | Nivel 3 (Oficial) | `ActionGroups/wave.d6a` |
| `right_shot\n`| Nivel 3 (Oficial) | `ActionGroups/right_shot.d6a` |
| `stand\n` | Nivel 3 (Oficial) | `ActionGroups/stand.d6a` |
| `walk_ready\n`| Nivel 3 (Oficial) | `ActionGroups/walk_ready.d6a` |
| `lie_to_stand\n`| Nivel 3 (Oficial) | `ActionGroups/lie_to_stand.d6a` |

---

## 4. Especificación del Canal de Visión (Puerto 8080)

- **URL de Conexión:** `http://<IP_ROBOT>:8080/stream?topic=/camera/image_raw`
- **Formato de Compresión:** MJPEG (Motion JPEG over HTTP Multipart).
- **Consumo en Cliente (`vision.py`):**
  - Utiliza `cv2.VideoCapture(url)` con limpieza de búfer (`time.sleep(0.8)`) para asegurar que el frame adquirido corresponda exactamente al instante posterior a la estabilización del cuello del robot y no a un búfer residual.
  - Para el ensamblado panorámico en el modo exploración, se redimensionan los 3 fotogramas a `320x240` px, se concatenan horizontalmente (`960x240`), se aplica ecualización adaptativa de histograma (**CLAHE**) para normalizar la iluminación y se añade padding simétrico para formar una imagen cuadrada perfecta (`960x960`) optimizada para la relación de aspecto del modelo **Qwen2.5-VL**.
