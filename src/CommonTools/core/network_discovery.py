import asyncio
import json
import socket
import logging
from asyncio import DatagramTransport
from typing import Optional

from psygnal import Signal

logger = logging.getLogger(__name__)

DISCOVERY_PORT = 55000
MAGIC_REQUEST = "WHO_IS_THE_MASTER?"


class MasterBeacon:
    class BeaconProtocol(asyncio.DatagramProtocol):
        def __init__(self, info):
            self.info = info
            self.response = json.dumps(info).encode()
            self.transport: Optional[DatagramTransport] = None
            super().__init__()
        
        def datagram_received(self, data, addr):
            if data.decode().strip() == MAGIC_REQUEST:
                self.transport.sendto(self.response, addr)
        
        def connection_made(self, transport):
            self.transport = transport
            sock = transport.get_extra_info('socket')
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except Exception:
                pass
    
    def __init__(self):
        self.transport = None
        self.port = DISCOVERY_PORT
        self._is_public = False
    
    async def start(self, ws_port, server_name="D&D Table"):
        loop = asyncio.get_running_loop()
        info = {
            "name": server_name,
            "ws_port": ws_port,
        }
        for port in range(DISCOVERY_PORT, DISCOVERY_PORT + 10):
            try:
                self.transport, _ = await loop.create_datagram_endpoint(
                    lambda: self.BeaconProtocol(info),
                    local_addr=('0.0.0.0', port),
                    allow_broadcast=True
                )
                self.port = port
                logger.info(f"Beacon successfully started on UDP port {port}")
                self._is_public = True
                return
            except OSError:
                continue
        
        raise RuntimeError("Could not bind Beacon to any port in range")
    
    def stop(self):
        if self.transport:
            self.transport.close()
        self._is_public = False
        
    @property
    def is_public(self):
        return self._is_public


class ServerScanner:
    server_found = Signal(dict)
    scan_finished = Signal()
    
    def __init__(self):
        self.found_servers = set()
    
    class ScannerProtocol(asyncio.DatagramProtocol):
        def __init__(self, scanner: "ServerScanner"):
            self.scanner = scanner
            self.transport = None
        
        def connection_made(self, transport):
            self.transport = transport
            sock = transport.get_extra_info('socket')
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                for port in range(DISCOVERY_PORT, DISCOVERY_PORT + 10):
                    try:
                        self.transport.sendto(MAGIC_REQUEST.encode(), ('127.0.0.1', port))
                    except PermissionError:
                        self.transport.sendto(MAGIC_REQUEST.encode(), ('255.255.255.255', port))
            except Exception:
                pass
        
        def datagram_received(self, data, addr):
            try:
                info = json.loads(data.decode())
                info['ip'] = addr[0]
                self.scanner.addServer(f"{info['ip']}:{info['ws_port']}", info)
            
            except Exception as e:
                logger.debug(f"Scan error: {e}")
    
    async def scan(self, timeout=2.0):
        loop = asyncio.get_running_loop()
        self.found_servers.clear()
        
        transport, _ = await loop.create_datagram_endpoint(
            lambda: self.ScannerProtocol(self),
            local_addr=('0.0.0.0', 0),
            allow_broadcast=True
        )
        
        try:
            await asyncio.sleep(timeout)
        finally:
            transport.close()
            self.scan_finished.emit()
    
    def addServer(self, server_key, info):
        if server_key not in self.found_servers:
            self.found_servers.add(server_key)
            self.server_found.emit(info)
