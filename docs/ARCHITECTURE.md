# 🏛️ Arquitectura del Sistema y Diseño de Software

Este documento detalla la arquitectura de software del sistema de interacción por voz y visión para el robot humanoide **AiNex ("Nelson")**, los patrones de diseño implementados, el modelo de concurrencia y los diagramas de interacción entre componentes.

---

## 1. Vista General de la Arquitectura

El sistema implementa una **Arquitectura en Capas Distribuidas (Distributed Layered Architecture)** desacoplada entre dos nodos computacionales principales conectados mediante una red de área local (TCP/IP):

```mermaid
graph TB
    subgraph Host_Node["Estación de Procesamiento Local (PC Host - GPU Accelerated)"]
        subgraph Presentation_Layer["Capa Sensorial y de Entrada"]
            SD["SoundDevice (16kHz Stream)"]
            CAM_IN["OpenCV VideoCapture (MJPEG Feed)"]
        end

        subgraph Core_Layer["Capa Cognitiva y de Procesamiento"]
            VAD_E["VAD Engine (Silero VAD ONNX)"]
            STT_E["STT Engine (Faster-Whisper CUDA / Google)"]
            NLP_E["NLP Engine (RapidFuzz WRatio / Levenshtein)"]
            TTS_E["TTS Engine (SAPI.SpVoice / pyttsx3)"]
            VIG_E["Vigilancia Facial (YuNet ONNX)"]
        end

        subgraph AI_Layer["Capa de Modelos Fundacionales"]
            VLM["Ollama Server (Qwen2.5-VL 3B Local)"]
        end

        subgraph Orchestration_Layer["Capa de Coordinación y Control"]
            MAIN["Orquestador Central (main.py)"]
            Q_AUDIO[("Queue: Segmentos Audio")]
            Q_CMD[("Queue: Comandos / Intents")]
            EV_EXPLORE[["Event: Modo Exploración"]]
            EV_STOP[["Event: Parada Emergencia"]]
        end

        subgraph Network_Client["Capa de Enlace con Hardware"]
            ROBOT_CLI["RobotClient (Socket TCP Client con Keep-Alive)"]
            ROBOT_VIS["RobotVision (Generador Panoramas 3-Vistas)"]
        end
    end

    subgraph Robot_Node["Nodo Embebido del Robot (Raspberry Pi - ROS Noetic)"]
        SOCK_SRV["T800_gait_client.py (TCP Server Port 9000)"]
        DISPATCHER{"Despachador en Cascada de 4 Niveles"}
        
        L1["Nivel 1: Hardware Base (GaitManager / Servos Cuello)"]
        L2["Nivel 2: Acciones Dinámicas (custom_actions/*.py)"]
        L3["Nivel 3: Cinemáticas Oficiales (MotionManager *.d6a)"]
        L4["Nivel 4: Fail-Safe Handler"]

        ROS_BUS["Bus de Servomotores Serie /dev/ttyAMA0"]
    end

    %% Flujos de datos
    SD --> VAD_E
    VAD_E -->|Voz Detectada| Q_AUDIO
    Q_AUDIO --> STT_E
    STT_E --> NLP_E
    NLP_E -->|Intent Clasificado| Q_CMD
    Q_CMD --> MAIN

    MAIN -->|Comandos de Movimiento| ROBOT_CLI
    MAIN -->|Síntesis Auditiva| TTS_E
    MAIN -->|Modo Exploración Activo| ROBOT_VIS
    ROBOT_VIS --> CAM_IN
    ROBOT_VIS -->|Panorama 3 Vistas| VLM
    VLM -->|Decisión de Giro/Avanzar| ROBOT_CLI

    MAIN -->|Inactividad > 45s| VIG_E
    VIG_E --> CAM_IN
    VIG_E -->|Rostro Detectado| ROBOT_CLI

    ROBOT_CLI <==|Socket TCP (Keep-Alive)|==> SOCK_SRV
    SOCK_SRV --> DISPATCHER
    DISPATCHER --> L1
    DISPATCHER --> L2
    DISPATCHER --> L3
    DISPATCHER --> L4
    L1 --> ROS_BUS
    L2 --> ROS_BUS
    L3 --> ROS_BUS
```

---

## 2. Patrones de Diseño Implementados

### 2.1. Patrón Productor-Consumidor Concurrente (Audio & VAD Pipeline)
Para garantizar que la escucha activa del micrófono **nunca se bloquee ni pierda frames** de audio mientras Whisper realiza inferencias pesadas, se implementó un pipeline desacoplado mediante colas de memoria (`queue.Queue`):
- **Hilo Productor (`AudioCapture`):** Lee chunks de audio de 32 ms a 16 kHz mediante `sounddevice.RawInputStream`. Alimenta los tensores al iterador de **Silero VAD**. Cuando detecta el inicio y fin de una frase de voz, deposita el buffer en `segmentos_pendientes`.
- **Hilo Consumidor (`hilo_procesamiento_voz`):** Extrae los buffers de audio, verifica que no hayan caducado (`MAX_ANTIGUEDAD_SEGMENTO_SEG = 6.0s`) y despacha la transcripción a los motores STT.

### 2.2. Patrón Despachador en Cascada de 4 Niveles (Cascade Dispatcher)
En el servidor del robot (`T800_gait_client.py`), las órdenes entrantes son evaluadas jerárquicamente:
1. **Nivel 1 (Hardware Base y Marcha):** Evalúa comandos directos de marcha en tiempo real (`adelante`, `atras`, `izquierda`, `derecha`, `parar`) y control de posición de cuello (`servo_arriba`, `servo_frente`, `servo_izquierda`, etc.) a través de `GaitManager`.
2. **Nivel 2 (Acciones Personalizadas Dinámicas):** Si el comando coincide con un script en `custom_actions/<comando>.py`, lo importa dinámicamente en tiempo de ejecución con `importlib.util` y ejecuta su función `run(gait_manager, setBusServoPulse, setServoPulse)`.
3. **Nivel 3 (Cinemáticas de Fábrica):** Si no es un script de Python, busca un archivo `.d6a` (base de datos SQLite de secuencias articulares) en `ActionGroups/` y lo delega a `MotionManager.runAction()`.
4. **Nivel 4 (Fail-Safe Graceful Degradation):** Si el comando no existe en ninguno de los niveles anteriores, registra una advertencia en log y responde sin cerrar el socket ni desestabilizar el bus de servos.

### 2.3. Patrón de Fallback Redundante (STT Concurrente)
El motor de transcripción ejecuta simultáneamente:
```python
future_whisper = executor.submit(_intentar_whisper, audio_bytes)
future_google = executor.submit(_intentar_google, audio_bytes)
```
- Se prioriza **Google Speech Recognition** si responde en menos de `GOOGLE_TIMEOUT_SEG = 7.0s` con texto válido.
- Si Google falla o se agota el tiempo por inestabilidad de red, se consume inmediatamente el resultado de **Faster-Whisper** ejecutado en GPU local (`beam_size=1`, búsqueda greedy para mínima latencia).

### 2.4. Inicialización Perezosa (Lazy Initialization)
Para componentes de visión pesados como el modelo **YuNet** de detección facial, la carga del modelo ONNX y la configuración de OpenCV se difieren hasta el momento en que se ejecuta la primera ronda de vigilancia pasiva. Esto optimiza el tiempo de arranque del sistema y previene conflictos de asignación de memoria con los contextos de CUDA de PyTorch.

---

## 3. Diagrama de Secuencia: Procesamiento de Comando de Voz

El siguiente diagrama detalla la interacción paso a paso desde que el usuario emite una orden verbal hasta que el robot la ejecuta físicamente:

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant Mic as Micrófono
    participant VAD as Silero VAD
    participant STT as STT Engine (Whisper/Google)
    participant NLP as NLP Engine
    participant Main as Orquestador (main.py)
    participant Socket as RobotClient (TCP)
    participant Robot as T800 Server (ROS)
    participant Servos as Bus de Servos

    Usuario->>Mic: "Nelson, ponte en guardia"
    Mic->>VAD: Stream PCM 16kHz
    Note over VAD: Detecta habla (Speech start... Speech end)
    VAD->>Main: Encola audio_bytes en segmentos_pendientes
    Main->>STT: transcribir_audio(audio_bytes)
    STT-->>Main: "nelson ponte en guardia"
    Main->>NLP: normalizar_texto() & contiene_wake_word()
    NLP-->>Main: Wake Word OK ('Nelson')
    Main->>NLP: clasificar_intencion("ponte en guardia")
    NLP-->>Main: Intent: 'guardia' (Score: 92.5)
    Main->>Socket: enviar_comando("guardia")
    Socket->>Robot: TCP Send: "guardia\n"
    Note over Robot: Despachador Cascada Nivel 2<br/>Carga custom_actions/guardia.py
    Robot->>Servos: gait_manager.disable()
    Robot->>Servos: setBusServoPulse(hombros, codos, muñecas)
    Servos-->>Robot: Postura de Guardia Adoptada
    Robot->>Servos: gait_manager.enable()
```

---

## 4. Máquina de Estados Finita (FSM) del Sistema

El robot transita entre diferentes estados operacionales gobernados por eventos de concurrencia (`threading.Event`):

```mermaid
stateDiagram-v2
    [*] --> Escucha_Activa: Inicialización Exitosa

    state Escucha_Activa {
        [*] --> Esperando_Voz
        Esperando_Voz --> Capturando_Habla: VAD Speech Start
        Capturando_Habla --> Procesando_Comando: VAD Speech End
        Procesando_Comando --> Esperando_Voz: Intent Procesado
    }

    Escucha_Activa --> Ejecutando_Accion: Intent Válido (ej: 'saluda', 'guardia')
    Ejecutando_Accion --> Escucha_Activa: Movimiento Completado

    Escucha_Activa --> Modo_Exploracion: Intent 'explora'
    state Modo_Exploracion {
        [*] --> Barrido_Camara
        Barrido_Camara --> Union_Panorama
        Union_Panorama --> Consulta_Qwen_VLM
        Consulta_Qwen_VLM --> Ejecutar_Paso_Marcha
        Ejecutar_Paso_Marcha --> Barrido_Camara
    }

    Modo_Exploracion --> Parada_Emergencia: Intent 'parar' / detener_evento.set()
    Ejecutando_Accion --> Parada_Emergencia: Intent 'parar'

    Escucha_Activa --> Patrullaje_Vigilancia: Inactividad > 45 segundos
    state Patrullaje_Vigilancia {
        [*] --> Mirar_Izquierda
        Mirar_Izquierda --> Analizar_YuNet_Izq
        Analizar_YuNet_Izq --> Mirar_Centro
        Mirar_Centro --> Analizar_YuNet_Centro
        Analizar_YuNet_Centro --> Mirar_Derecha
        Mirar_Derecha --> Analizar_YuNet_Der
        Analizar_YuNet_Der --> Accion_Saludo: Rostro Encontrado
        Accion_Saludo --> [*]
        Analizar_YuNet_Der --> [*]: Sin Rostros
    }
    Patrullaje_Vigilancia --> Escucha_Activa: Patrullaje Finalizado

    Parada_Emergencia --> Escucha_Activa: Reset de Eventos
```
