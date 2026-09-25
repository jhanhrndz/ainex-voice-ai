#!/usr/bin/env python3
"""
Script para encontrar automáticamente la IP del Robot HiWonder AiNex en la red local.
Soporta redes empresariales con múltiples subredes (como Audacia 172.16.x.x).
Inspirado en la arquitectura modular de ORION.
"""

import socket
import subprocess
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

IP_FALLBACK_DEFAULT = "192.168.149.1"  # IP por defecto en modo AP / Hotspot
PUERTO_SOCKET_ROBOT = 9000
PUERTO_CAMERA_ROBOT = 8080
PUERTO_DISCOVERY_UDP = 9027

# Subredes conocidas de la red Audacia donde el robot puede caer
AUDACIA_SUBNETS = list(range(120, 131))  # 172.16.120.x a 172.16.130.x


def get_local_ip() -> str:
    """Obtiene la IP local de la máquina actual."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "192.168.149.100"


def get_network_ranges() -> List[str]:
    """
    Obtiene la lista de IPs a escanear.
    Si estamos en la red Audacia (172.16.x.x), escanea múltiples subredes.
    """
    local_ip = get_local_ip()
    all_ips = []

    if local_ip.startswith("172.16."):
        # Red Audacia: escanear subredes 172.16.120.x a 172.16.130.x
        for subnet in AUDACIA_SUBNETS:
            network = ipaddress.IPv4Network(f"172.16.{subnet}.0/24", strict=False)
            all_ips.extend([str(ip) for ip in network.hosts()])
    else:
        # Red estándar: escanear solo la subred local /24
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        all_ips = [str(ip) for ip in network.hosts()]

    return all_ips


def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    """Verifica si un puerto TCP está abierto en la IP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except Exception:
        return False


def validar_robot(ip: str) -> bool:
    """
    Validación estricta: confirma que la IP pertenece al robot AiNex.
    Requiere puerto 9000 (T800_gait_client) + puerto 22 (SSH Ubuntu).
    """
    return check_port(ip, PUERTO_SOCKET_ROBOT, 0.8) and check_port(ip, 22, 0.8)


def discover_by_arp(mostrar_logs: bool = True) -> Optional[str]:
    """
    Nivel 0: Búsqueda instantánea en la tabla ARP de Windows.
    Revisa todos los dispositivos que el sistema ya conoce sin hacer escaneo.
    """
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True, text=True, timeout=5
        )
        # Extraer todas las IPs 172.16.x.x de la tabla ARP
        candidatos = []
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                ip = parts[0]
                if ip.startswith("172.16.") or ip.startswith("192.168."):
                    candidatos.append(ip)

        if candidatos and mostrar_logs:
            print(f"   📋 {len(candidatos)} IPs encontradas en tabla ARP")

        # Validar cuáles son el robot (puerto 9000 + SSH)
        for ip in candidatos:
            if validar_robot(ip):
                return ip
    except Exception:
        pass
    return None


def discover_by_udp(timeout: float = 1.5) -> Optional[str]:
    """
    Nivel 1: Descubrimiento por UDP Broadcast HiWonder (puerto 9027).
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)
            s.sendto(b"LOBOT_NET_DISCOVER", ("<broadcast>", PUERTO_DISCOVERY_UDP))

            start_time = time.time()
            while time.time() - start_time < timeout:
                data, addr = s.recvfrom(1024)
                msg = data.decode("utf-8", errors="ignore")
                if "AiNex" in msg or "SPIDER" in msg or "HW-" in msg:
                    return addr[0]
    except Exception:
        pass
    return None


def buscar_ip_robot(mostrar_logs: bool = True) -> str:
    """
    Busca automáticamente la IP del robot en la red local.
    Si no lo encuentra, retorna la IP de respaldo '192.168.149.1'.
    """
    local_ip = get_local_ip()
    if mostrar_logs:
        print(f"🔍 Buscando Robot HiWonder AiNex en la red local...")
        print(f"   🌐 IP local de tu laptop: {local_ip}")

    # --- NIVEL 0: Búsqueda Instantánea en Tabla ARP ---
    if mostrar_logs:
        print("📋 [Nivel 0] Revisando tabla ARP del sistema...")
    ip_arp = discover_by_arp(mostrar_logs)
    if ip_arp:
        if mostrar_logs:
            print(f"🎉 ¡Robot encontrado en tabla ARP: {ip_arp}!")
        return ip_arp

    # --- NIVEL 1: Descubrimiento por UDP Broadcast ---
    if mostrar_logs:
        print("⚡ [Nivel 1] Probando Broadcast UDP HiWonder...")
    ip_udp = discover_by_udp(timeout=1.5)
    if ip_udp:
        if mostrar_logs:
            print(f"🎉 ¡Robot encontrado por Broadcast UDP en: {ip_udp}!")
        return ip_udp

    # --- NIVEL 2: Probar IPs Conocidas / Históricas ---
    known_ips = [
        "172.16.123.86", "172.16.123.147", "172.16.126.78",
        "172.16.121.9", "192.168.149.1", "192.168.1.100"
    ]
    if mostrar_logs:
        print("🎯 [Nivel 2] Probando IPs conocidas recientes...")
    for ip in known_ips:
        if validar_robot(ip):
            if mostrar_logs:
                print(f"🎉 ¡Robot validado en IP conocida: {ip}!")
            return ip

    # --- NIVEL 3: Escaneo Masivo Multi-Subred (Estilo ORION) ---
    network_ips = get_network_ranges()
    if network_ips:
        es_audacia = local_ip.startswith("172.16.")
        if mostrar_logs:
            if es_audacia:
                print(f"📡 [Nivel 3] Escaneando {len(network_ips)} IPs en subredes de Audacia (172.16.{AUDACIA_SUBNETS[0]}-{AUDACIA_SUBNETS[-1]}.x)...")
            else:
                print(f"📡 [Nivel 3] Escaneando {len(network_ips)} IPs en subred local ({local_ip}/24)...")

        # Fase A: Escaneo rápido de puertos en paralelo
        candidatos = []
        with ThreadPoolExecutor(max_workers=100) as executor:
            future_to_ip = {
                executor.submit(check_port, ip, PUERTO_SOCKET_ROBOT, 0.5): ip
                for ip in network_ips
            }
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        candidatos.append(ip)
                        if mostrar_logs:
                            print(f"   👉 Puerto {PUERTO_SOCKET_ROBOT} activo en {ip}")
                except Exception:
                    pass

        # Fase B: Validación estricta de candidatos (puerto 9000 + SSH 22)
        for ip in candidatos:
            if validar_robot(ip):
                if mostrar_logs:
                    print(f"🎉 ¡Robot validado y encontrado en: {ip}!")
                return ip

    # --- NIVEL 4: Fallback por Defecto a Modo Hotspot ---
    if mostrar_logs:
        print(f"⚠️ No se encontró al robot. Usando IP de respaldo (Hotspot): {IP_FALLBACK_DEFAULT}")
    return IP_FALLBACK_DEFAULT


def main():
    print("=" * 55)
    print("🤖 BUSCADOR AUTOMÁTICO DE IP - ROBOT AINEX")
    print("=" * 55)

    start = time.time()
    ip_encontrada = buscar_ip_robot(mostrar_logs=True)
    elapsed = time.time() - start

    print("\n" + "=" * 55)
    print(f"✅ IP FINAL ASIGNADA: {ip_encontrada}")
    print(f"🔌 Socket Control: {ip_encontrada}:{PUERTO_SOCKET_ROBOT}")
    print(f"⏱️  Tiempo de búsqueda: {elapsed:.1f} segundos")
    print("=" * 55)


if __name__ == "__main__":
    main()
