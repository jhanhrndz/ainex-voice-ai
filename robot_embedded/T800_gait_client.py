#!/usr/bin/env python3
# encoding: utf-8
"""
Control de Marcha T800 para Robot HIWONDER - NELSON
Servidor TCP Modular con Despachador en Cascada de 4 Niveles:
1. Hardware base y marcha en tiempo real (GaitManager / Servos cuello)
2. Acciones personalizadas dinámicas (custom_actions/: .py / .d6a)
3. Cinemáticas oficiales de fábrica (ActionGroups/: .d6a)
4. Fail-Safe sin desconexión de socket
"""

import os
import sys
import time
import socket
import importlib.util
from time import sleep

import rospy
from ainex_kinematics.gait_manager import GaitManager
from ainex_kinematics.motion_manager import MotionManager
from servo_controller import *

# Inicializar nodo ROS
rospy.init_node('tcp_gait_server')
gait_manager = GaitManager()
rospy.sleep(0.2)

# Rutas de cinemáticas
ACTION_GROUPS_DIR = '/home/ubuntu/software/ainex_controller/ActionGroups'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_ACTIONS_DIR = os.path.join(BASE_DIR, 'custom_actions')

# Inicializar MotionManager oficial de Hiwonder
try:
    official_motion_manager = MotionManager(ACTION_GROUPS_DIR)
except Exception as e:
    rospy.logwarn(f"No se pudo cargar MotionManager oficial ({ACTION_GROUPS_DIR}): {e}")
    official_motion_manager = None

# Inicializar MotionManager para custom_actions
try:
    if not os.path.exists(CUSTOM_ACTIONS_DIR):
        os.makedirs(CUSTOM_ACTIONS_DIR)
    custom_motion_manager = MotionManager(CUSTOM_ACTIONS_DIR)
except Exception as e:
    rospy.logwarn(f"No se pudo cargar MotionManager para custom_actions: {e}")
    custom_motion_manager = None


def mover_camara(direccion_camara):
    """Mueve el servo horizontal 23 de la cámara."""
    posicion = {
        "servo_derecha": 250,
        "servo_centro": 500,
        "servo_izquierda": 750
    }.get(direccion_camara.lower())

    if posicion is not None:
        setServoPulse(23, posicion, 1000)
        sleep(1)
        rospy.loginfo(f"📸 Cámara movida a {direccion_camara.upper()} ({posicion})")
    else:
        rospy.logwarn(f"⚠️ Comando de cámara no reconocido: {direccion_camara}")


def inclinar_cabeza(inclinacion):
    """Controla el servo vertical 24 de la cabeza."""
    pulso = {
        "servo_arriba": 630,
        "servo_frente": 500,
        "servo_abajo": 350
    }.get(inclinacion.lower())

    if pulso is not None:
        setServoPulse(24, pulso, 800)
        sleep(0.8)
        rospy.loginfo(f"↕️ Cuello vertical a {inclinacion.upper()} ({pulso})")
    else:
        rospy.logwarn(f"⚠️ Comando de inclinación no reconocido: {inclinacion}")


def ejecutar_accion_python(ruta_script):
    """Carga y ejecuta dinámicamente un script Python personalizado."""
    try:
        nombre = os.path.basename(ruta_script)
        rospy.loginfo(f"🐍 [Nivel 2] Ejecutando acción Python: {nombre}...")
        spec = importlib.util.spec_from_file_location("custom_action_module", ruta_script)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        if hasattr(modulo, "run"):
            import inspect
            sig = inspect.signature(modulo.run)
            if len(sig.parameters) >= 3:
                modulo.run(gait_manager, setBusServoPulse, setServoPulse)
            else:
                modulo.run(gait_manager, setBusServoPulse)
            rospy.loginfo(f"✅ Acción Python completada con éxito: {nombre}")
        else:
            rospy.logwarn(f"⚠️ El script {nombre} no tiene función 'run(gait_manager, setBusServoPulse)'")
    except Exception as e:
        rospy.logerr(f"❌ Error ejecutando acción Python {ruta_script}: {e}")
        try:
            gait_manager.enable()
        except Exception:
            pass


def ejecutar_accion_motion(manager, nombre_accion):
    """Ejecuta un grupo de acción .d6a desactivando temporalmente la marcha."""
    gait_manager.stop()
    gait_manager.disable()
    if manager:
        try:
            rospy.loginfo(f"🎬 Ejecutando cinemática .d6a: '{nombre_accion}'...")
            manager.run_action(nombre_accion)
            rospy.loginfo(f"✅ Cinemática completada: '{nombre_accion}'")
        except Exception as e:
            rospy.logwarn(f"❌ Error al ejecutar cinemática {nombre_accion}: {e}")
    else:
        rospy.logwarn("MotionManager no está disponible.")
    gait_manager.enable()


def ejecutar_comando(comando):
    """Despachador en cascada de 4 niveles."""
    comando = comando.lower().strip()
    if not comando:
        return
    rospy.loginfo("Comando recibido por socket: %s", comando)

    # -------------------------------------------------------------
    # NIVEL 1: Hardware base y marcha (Crítico / Tiempo Real)
    # -------------------------------------------------------------
    if comando in ["servo_derecha", "servo_centro", "servo_izquierda"]:
        mover_camara(comando)
        return
    elif comando in ["servo_arriba", "servo_frente", "servo_abajo"]:
        inclinar_cabeza(comando)
        return
    elif comando in ["parar", "stop", "detener"]:
        gait_manager.stop()
        rospy.loginfo("🛑 Movimiento detenido")
        return
    elif comando == "adelante":
        gait_manager.move(3, 0.02, 0, 0)
        rospy.sleep(3)
        gait_manager.stop()
        return
    elif comando == "atras":
        gait_manager.move(3, -0.02, 0, 0)
        rospy.sleep(3)
        gait_manager.stop()
        return
    elif comando == "izquierda":
        gait_manager.move(3, 0.02, 0, 8)
        rospy.sleep(3)
        gait_manager.stop()
        return
    elif comando == "derecha":
        gait_manager.move(3, 0.02, 0, -8)
        rospy.sleep(3)
        gait_manager.stop()
        return

    # Normalizar identificador para búsqueda en carpetas
    nombre_limpio = comando.replace(".py", "").replace(".d6a", "").replace(" ", "_")

    # -------------------------------------------------------------
    # NIVEL 2: Acciones personalizadas (custom_actions/ - Máxima prioridad)
    # -------------------------------------------------------------
    # 2A. Script Python (.py)
    ruta_custom_py = os.path.join(CUSTOM_ACTIONS_DIR, f"{nombre_limpio}.py")
    if os.path.exists(ruta_custom_py):
        ejecutar_accion_python(ruta_custom_py)
        return

    # 2B. Cinemática .d6a en custom_actions/
    ruta_custom_d6a = os.path.join(CUSTOM_ACTIONS_DIR, f"{nombre_limpio}.d6a")
    if os.path.exists(ruta_custom_d6a):
        rospy.loginfo(f"📁 [Nivel 2] Cinemática propia detectada: {nombre_limpio}.d6a")
        ejecutar_accion_motion(custom_motion_manager, nombre_limpio)
        return

    # -------------------------------------------------------------
    # NIVEL 3: Cinemáticas oficiales de Hiwonder (/ActionGroups/)
    # -------------------------------------------------------------
    alias_oficiales = {
        "saluda": "greet",
        "saludar": "greet",
        "greet": "greet",
        "baila": "twist",
        "bailar": "twist",
        "baile": "twist",
        "twist": "twist",
        "pase_robot": "wave",
        "pase": "wave",
        "pase_del_robot": "wave",
        "wave": "wave",
        "ola": "wave",
        "stand": "stand",
        "firmes": "stand",
        "parate": "stand",
        "walk_ready": "walk_ready",
        "listo": "walk_ready",
        "posicion_caminar": "walk_ready",
        "patea": "right_shot",
        "patea_der": "right_shot",
        "right_shot": "right_shot",
        "patada_derecha": "right_shot",
        "patea_izq": "left_shot",
        "left_shot": "left_shot",
        "patada_izquierda": "left_shot",
        "levantate": "lie_to_stand",
        "recuperate": "lie_to_stand",
        "lie_to_stand": "lie_to_stand",
        "brazos_atras": "hand_back",
        "hand_back": "hand_back",
        "abre_brazos": "hand_open",
        "hand_open": "hand_open"
    }

    accion_target = alias_oficiales.get(nombre_limpio, nombre_limpio)
    ruta_oficial_d6a = os.path.join(ACTION_GROUPS_DIR, f"{accion_target}.d6a")
    if os.path.exists(ruta_oficial_d6a):
        rospy.loginfo(f"📚 [Nivel 3] Cinemática oficial Hiwonder: {accion_target}.d6a")
        ejecutar_accion_motion(official_motion_manager, accion_target)
        return

    # -------------------------------------------------------------
    # NIVEL 4: Fail-Safe (Comando no reconocido)
    # -------------------------------------------------------------
    rospy.logwarn(f"⚠️ Comando no reconocido en ningún nivel: '{comando}'")


# Configurar servidor TCP persistente
HOST = '0.0.0.0'
PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
sock.listen(5)

rospy.loginfo("Servidor TCP escuchando en puerto %d...", PORT)

try:
    while not rospy.is_shutdown():
        try:
            rospy.loginfo("Esperando conexión de cliente...")
            conn, addr = sock.accept()
            conn.settimeout(None)
            rospy.loginfo("Conexión aceptada desde %s", addr)

            with conn:
                buffer = ""
                while not rospy.is_shutdown():
                    try:
                        data = conn.recv(1024)
                        if not data:
                            rospy.logwarn("Cliente desconectado.")
                            break
                        buffer += data.decode('utf-8')
                        while '\n' in buffer:
                            linea_comando, buffer = buffer.split('\n', 1)
                            comando_limpio = linea_comando.strip()
                            if comando_limpio:
                                ejecutar_comando(comando_limpio)
                    except socket.timeout:
                        continue
                    except (ConnectionResetError, BrokenPipeError):
                        rospy.logwarn("Conexión reiniciada por el cliente.")
                        break
        except socket.timeout:
            continue
        except Exception as e:
            if not rospy.is_shutdown():
                rospy.logwarn(f"Aviso de conexión: {e}")
            time.sleep(1)

except KeyboardInterrupt:
    rospy.loginfo("Interrupción por teclado. Cerrando servidor...")
finally:
    try:
        sock.close()
    except Exception:
        pass
    rospy.loginfo("Socket cerrado.")
