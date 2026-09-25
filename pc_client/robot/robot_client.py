import socket
import threading
import time
from config.settings import DIR_IP, ROBOT_PORT

class RobotClient:
    def __init__(self):
        print('[INFO] Iniciando controlador de dirección con autoreconexión...')
        self.lock = threading.Lock()
        self.sock = None
        self._conectar_socket()

    def _conectar_socket(self):
        """Cierra el socket anterior si existía y abre una nueva conexión con Keep-Alive."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        try:
            nuevo_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            nuevo_sock.settimeout(5.0)
            
            # Habilitar TCP Keep-Alive
            nuevo_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # En Windows: sondeo cada 5s de inactividad, intervalo 2s
            if hasattr(socket, 'SIO_KEEPALIVE_VALS'):
                nuevo_sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 5000, 2000))

            nuevo_sock.connect((DIR_IP, ROBOT_PORT))
            nuevo_sock.settimeout(None)  # Quitar timeout para operaciones normales
            self.sock = nuevo_sock
            print('[INFO] 🔗 Conexión por socket establecida correctamente con el robot.')
            return True
        except Exception as e:
            print(f'[ERROR] No se pudo conectar al robot en {DIR_IP}:{ROBOT_PORT}: {e}')
            self.sock = None
            return False

    def _enviar_con_reintento(self, payload, reintentos=3):
        """Envía datos por el socket con reconexión automática si se interrumpió el enlace."""
        with self.lock:
            for intento in range(reintentos):
                if self.sock is None:
                    print('[INFO] 🔄 Reabriendo conexión con el robot...')
                    if not self._conectar_socket():
                        time.sleep(0.5)
                        continue

                try:
                    self.sock.sendall(payload.encode('utf-8'))
                    return True
                except (socket.error, BrokenPipeError, ConnectionResetError, OSError) as e:
                    print(f'[ADVERTENCIA] ⚠️ Enlace TCP interrumpido ({e}). Reconectando (intento {intento + 1}/{reintentos})...')
                    self._conectar_socket()
                    time.sleep(0.3)

            print(f'[ERROR] ❌ No se pudo enviar el comando tras {reintentos} intentos.')
            return False

    def enviar_comando(self, direccion):
        comando = f"{direccion}\n"
        if self._enviar_con_reintento(comando):
            print(f'[INFO] ➡️ Comando enviado al robot: {direccion}')

    def mover_camara(self, posicion):
        comando = f"servo_{posicion}\n"
        if self._enviar_con_reintento(comando):
            # Pausa para que el robot se estabilice físicamente tras el giro
            time.sleep(1.2)

    def inclinar_camara(self, inclinacion):
        """Envía servo_arriba o servo_frente al robot."""
        comando = f"servo_{inclinacion}\n"
        if self._enviar_con_reintento(comando):
            time.sleep(0.8)

    def cerrar(self):
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                    print('[INFO] Socket cerrado.')
                except Exception:
                    pass
                self.sock = None
