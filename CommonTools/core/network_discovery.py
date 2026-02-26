import asyncio
import json
import socket
from loguru import logger
from psygnal import Signal

DISCOVERY_PORT = 55000  # Используем тот, который свободен
MAGIC_REQUEST = "WHO_IS_THE_MASTER?"


# --- МАЯК МАСТЕРА (ОТВЕЧАЕТ) ---
class MasterBeacon:
    def __init__(self):
        self.transport = None
    
    async def start(self, ip_list, ws_port, http_port, server_name="D&D Table"):
        loop = asyncio.get_running_loop()
        
        info = {
            "name": server_name,
            "ip": ip_list[0] if ip_list else "0.0.0.0",  # Для ответа нужен конкретный IP
            "ws_port": ws_port,
            "http_port": http_port
        }
        
        # Внутренний протокол для маяка
        class BeaconProtocol(asyncio.DatagramProtocol):
            def datagram_received(self, data, addr):
                if data.decode().strip() == MAGIC_REQUEST:
                    response = json.dumps(info).encode()
                    self.transport.sendto(response, addr)
            
            def connection_made(self, transport):
                self.transport = transport
                # Эта настройка не обязательна для ответа, но пусть будет
                sock = transport.get_extra_info('socket')
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                except Exception:
                    pass
        
        try:
            self.transport, _ = await loop.create_datagram_endpoint(
                BeaconProtocol,
                local_addr=('0.0.0.0', DISCOVERY_PORT),
                allow_broadcast=True
            )
            logger.info(f"Beacon started on UDP {DISCOVERY_PORT}")
        except OSError:
            logger.warning(f"Beacon port {DISCOVERY_PORT} busy")
    
    def stop(self):
        if self.transport:
            self.transport.close()


class ServerScanner:
    server_found = Signal(dict)
    scan_finished = Signal()
    
    async def scan(self, timeout=2.0):
        loop = asyncio.get_running_loop()
        found_servers = set()
        
        class ScannerProtocol(asyncio.DatagramProtocol):
            def __init__(self, on_found):
                self.on_found = on_found
                self.transport = None
            
            def connection_made(self, transport):
                self.transport = transport
                sock = transport.get_extra_info('socket')
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    self.transport.sendto(MAGIC_REQUEST.encode(), ('127.0.0.1', DISCOVERY_PORT))
                except PermissionError:
                    self.transport.sendto(MAGIC_REQUEST.encode(), ('255.255.255.255', DISCOVERY_PORT))
                except Exception:
                    pass
            
            def datagram_received(self, data, addr):
                try:
                    info = json.loads(data.decode())
                    info['real_ip'] = addr[0]  # Всегда берем реальный IP
                    info['ip'] = addr[0]  # И заменяем им внутренний
                    
                    # Ключ для уникальности (IP:Port)
                    server_key = f"{info['ip']}:{info['ws_port']}"
                    if server_key not in found_servers:
                        found_servers.add(server_key)
                        self.on_found(info)
                
                except Exception as e:
                    logger.debug(f"Scan error: {e}")
        
        # Создаем эндпоинт сканера
        transport, _ = await loop.create_datagram_endpoint(
            lambda: ScannerProtocol(self.server_found.emit),
            local_addr=('0.0.0.0', 0),  # Любой свободный порт
            allow_broadcast=True
        )
        
        try:
            await asyncio.sleep(timeout)
        finally:
            transport.close()
            self.scan_finished.emit()


if __name__ == "__main__":
    async def test_discovery():
        print("--- ЗАПУСК ТЕСТА (надежная версия) ---")
        
        beacon = MasterBeacon()
        await beacon.start(ip_list=["192.168.1.100"], ws_port=8765, http_port=8080, server_name="TEST_SERVER")
        
        scanner = ServerScanner()
        
        scanner.server_found.connect(lambda info: print(f"✅ НАЙДЕН СЕРВЕР: {info}"))
        
        print("🔍 Сканируем 3 секунды...")
        await scanner.scan(timeout=3.0)
        
        beacon.stop()
        print("--- ТЕСТ ЗАВЕРШЕН ---")
    
    
    try:
        asyncio.run(test_discovery())
    except KeyboardInterrupt:
        pass
