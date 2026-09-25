# 🚀 Guía de Despliegue, Configuración e Instalación en Producción

Esta guía contiene los pasos necesarios para instalar, configurar y desplegar el sistema desde cero tanto en la estación de trabajo PC Host como en el sistema embebido del robot humanoide **AiNex**.

---

## 1. Requisitos de Infraestructura y Red

### 1.1. Topología de Red
- La PC Host y el robot deben estar conectados a la **misma red de área local (LAN)** (mediante router Wi-Fi de 5 GHz o switch Ethernet).
- Se recomienda asignar una **IP estática** o reserva DHCP al robot (por ejemplo: `192.168.1.13` o `192.168.149.1`).

### 1.2. Puertos de Red Requeridos
Asegúrate de que los siguientes puertos no estén bloqueados por firewalls:
- `TCP 9000`: Canal de comandos del servidor `T800_gait_client.py`.
- `TCP 8080`: Flujo de video MJPEG de la cámara ROS (`web_video_server`).
- `TCP 22`: Acceso SSH para administración remota y transferencia SCP.
- `TCP 11434`: API local de Ollama en la PC Host.

---

## 2. Configuración de la Estación de Trabajo (PC Host)

### 2.1. Prerrequisitos de Software
- **Sistema Operativo:** Windows 10/11 (64-bit) o Ubuntu 22.04 LTS.
- **Python:** Versión `3.10.x` o superior.
- **Drivers de GPU:** NVIDIA CUDA Toolkit 11.8 o 12.x con controladores actualizados.
- **Ollama:** Descargar e instalar desde [ollama.ai](https://ollama.ai/).

### 2.2. Instalación del Entorno Virtual y Dependencias
Abre una terminal de PowerShell (o Bash) en el directorio del proyecto:

```powershell
# 1. Crear el entorno virtual de Python
python -m venv .venv

# 2. Activar el entorno virtual
# En Windows:
.\.venv\Scripts\Activate.ps1
# En Linux:
source .venv/bin/activate

# 3. Instalar PyTorch con aceleración CUDA
# (Ajustar según la versión de CUDA instalada, ejemplo para CUDA 12.1):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 4. Instalar las dependencias del proyecto
pip install -r requirements.txt
```

### 2.3. Configuración y Pre-calentamiento del Modelo VLM
Descarga el modelo de visión multimodal en Ollama:
```powershell
ollama pull qwen2.5vl:3b
```
Verifica que el servicio esté corriendo en segundo plano:
```powershell
curl http://localhost:11434/api/tags
```

### 2.4. Ajuste de Parámetros de Red
Edita `pc_client/config/settings.py` e ingresa la dirección IP de tu robot:
```python
DIR_IP = '192.168.1.13' # Dirección IP asignada al AiNex
ROBOT_PORT = 9000
```

---

## 3. Configuración del Robot Embebido (AiNex - Raspberry Pi)

### 3.1. Transferencia de Archivos al Robot
Desde tu PC Host, transfiere los archivos necesarios a la ruta de trabajo de ROS del robot mediante SCP:

```powershell
# Transferir el script servidor y la carpeta de acciones personalizadas
scp robot_embedded/T800_gait_client.py ubuntu@<IP_ROBOT>:/home/ubuntu/ros_ws/src/ainex_tutorial/scripts/gait_control/
scp -r robot_embedded/custom_actions ubuntu@<IP_ROBOT>:/home/ubuntu/ros_ws/src/ainex_tutorial/scripts/gait_control/
scp robot_embedded/ainex-gait.service ubuntu@<IP_ROBOT>:/home/ubuntu/
```

### 3.2. Configuración del Demonio `systemd` (Arranque Automático)
Accede por SSH a la Raspberry Pi del robot:
```bash
ssh ubuntu@<IP_ROBOT>
```

Instala y activa el servicio para que el servidor de control se inicie automáticamente cada vez que el robot se encienda:
```bash
# Copiar el archivo de servicio a la ruta del sistema
sudo cp /home/ubuntu/ainex-gait.service /etc/systemd/system/

# Recargar los demonios de systemd
sudo systemctl daemon-reload

# Habilitar el servicio en el inicio del sistema
sudo systemctl enable ainex-gait.service

# Iniciar el servicio inmediatamente
sudo systemctl start ainex-gait.service

# Verificar el estado operativo del servicio
sudo systemctl status ainex-gait.service
```

### 3.3. Monitoreo y Diagnóstico del Servicio en el Robot
Para observar en tiempo real los comandos que recibe el robot y la salida de los despachadores:
```bash
journalctl -u ainex-gait.service -f
```

---

## 4. Prueba de Humo y Puesta en Marcha (Smoke Test)

Sigue esta lista de verificación para confirmar que todo el sistema opera correctamente:

1. **Encendido:** Enciende el robot AiNex y espera 45 segundos a que la Raspberry Pi cargue Ubuntu, inicie `roscore` y active `ainex-gait.service`.
2. **Ping de Red:** Desde la PC Host, ejecuta `ping <IP_ROBOT>` y verifica que la latencia sea <10 ms.
3. **Flujo de Video:** Abre un navegador en la PC e ingresa a `http://<IP_ROBOT>:8080/stream?topic=/camera/image_raw`. Deberás ver la transmisión en vivo de la cámara.
4. **Ejecución del Cliente:**
   ```powershell
   cd pc_client
   python main.py
   ```
5. **Validación:**
   - La terminal mostrará: `[INFO] Faster-Whisper cargado en GPU`, `[INFO] Silero VAD listo` y `[INFO] Conexión por socket establecida`.
   - Di: *"Nelson, saluda"*. El robot deberá responder físicamente con el movimiento de bienvenida.
   - Di: *"Nelson, ponte en guardia"*. El robot flexionará los codos y levantará los brazos en postura de boxeo.
   - Di: *"Nelson, para"*. El robot se detendrá de inmediato.

---

## 5. Solución de Problemas Frecuentes (Troubleshooting)

### Error: `No se pudo conectar al robot en 192.168.x.x:9000`
- **Causa:** El servicio `ainex-gait.service` no está corriendo en el robot o la IP cambió.
- **Solución:** Conéctate por SSH al robot y ejecuta `sudo systemctl restart ainex-gait.service`. Verifica con `hostname -I` la IP actual del robot.

### Error: `CUDA out of memory` en la PC Host
- **Causa:** La VRAM de la GPU está saturada por tener múltiples modelos cargados.
- **Solución:** En `pc_client/config/settings.py`, cambia `MODEL_SIZE = "small"` por `"tiny"` o `"base"`, o define `DEVICE_WHISPER = "cpu"` para que Whisper use la memoria RAM convencional mientras Qwen2.5-VL utiliza la GPU.

### Advertencia: `[Descartado por antigüedad] segmento de hace X.Xs`
- **Causa:** La cola de audio se saturó porque el motor de transcripción tardó más del tiempo límite en procesar comandos continuos.
- **Solución:** Es el mecanismo de protección del sistema para no procesar órdenes desfasadas. No requiere acción correctiva.
