import asyncio
import json
import socket
import logging
import time
import struct
import uuid
from asyncio import DatagramTransport
from typing import Optional, Dict, Set, Self

from attrs import define, field
from psygnal import Signal

from CommonTools.version import __version__

logger = logging.getLogger(__name__)

# Константы протокола
DISCOVERY_PORT = 55000
MULTICAST_GROUP = "224.0.2.60"
MAGIC_REQUEST = "WHO_IS_THE_MASTER?"
PROTOCOL_SIG = f"DDTABLE:{__version__}"
MAX_PACKET_SIZE = 1400


@define(hash=True, eq=True)
class ServerEntry:
    uid: str
    name: str
    port: int
    addresses: set[str] = field(hash=False, eq=False)
    last_seen: float = field(hash=False, eq=False)
    
    @classmethod
    def create(cls, uid: str, info: dict) -> Self:
        return cls(
            uid, info.get("name", "Unknown"),
            info.get("ws_port"), set(), time.time()
        )
    
    def __iadd__(self, address: str):
        self.addresses.add(address)
        self.last_seen = time.time()
        return self
    
    @staticmethod
    def _priority_address(ip: str):
        if ip.startswith("127.") or ip == "::1":
            return 4
        if ip.startswith(("192.168.", "10.", "172.16.")):
            return 3
        if ip.startswith(("100.", "26.", "25.")):
            return 2
        return 1
    
    def get_best_address(self) -> str:
        """Выбирает приоритетный IP для подключения."""
        return max(self.addresses, key=self._priority_address)
    
    def pack(self):
        return dict(
            uid=self.uid,
            name=self.name,
            best_ip=self.get_best_address(),
            ws_port=self.port,
            all_addresses=list(self.addresses)
        )


class MasterBeacon:
    class BeaconProtocol(asyncio.DatagramProtocol):
        def __init__(self, info: dict):
            self.info = info
            self.info["_sig"] = PROTOCOL_SIG
            self.response = json.dumps(self.info).encode('utf-8')
            self.transport: Optional[DatagramTransport] = None
            
            if len(self.response) > MAX_PACKET_SIZE:
                logger.warning(f"Payload too large ({len(self.response)} bytes), discovery might fail.")
            super().__init__()
        
        def connection_made(self, transport):
            self.transport = transport
            sock = transport.get_extra_info('socket')
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
                
                mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except Exception as e:
                logger.debug(f"Socket options setup warning: {e}")
        
        def datagram_received(self, data: bytes, addr):
            try:
                message = data.decode('utf-8').strip()
                if message == MAGIC_REQUEST:
                    if len(self.response) <= MAX_PACKET_SIZE:
                        # Отвечаем напрямую отправителю (Unicast)
                        self.transport.sendto(self.response, addr)
                        # Дублируем в Multicast группу для надежности в VLAN
                        self.transport.sendto(self.response, (MULTICAST_GROUP, DISCOVERY_PORT))
            except (UnicodeDecodeError, Exception) as e:
                logger.debug(f"Beacon receive error: {e}")
    
    def __init__(self):
        self.transport = None
        self._uid = uuid.uuid4().hex[:8]
        self.port = DISCOVERY_PORT
        self._is_public = False
    
    async def start(self, ws_port: int, server_name: str = "D&D Table"):
        loop = asyncio.get_running_loop()
        info = {"name": server_name, "ws_port": ws_port, "uid": self._uid}
        
        for port in range(DISCOVERY_PORT, DISCOVERY_PORT + 10):
            try:
                self.transport, _ = await loop.create_datagram_endpoint(
                    lambda: self.BeaconProtocol(info),
                    local_addr=('0.0.0.0', port),
                    allow_broadcast=True
                )
                self.port = port
                logger.info(f"Beacon started on UDP {port} (Broadcast/Multicast active)")
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
        self.found_servers: dict[str, ServerEntry] = {}
        self._last_seen: Dict[str, float] = {}  # Для дедупликации (30 сек)
    
    class ScannerProtocol(asyncio.DatagramProtocol):
        def __init__(self, scanner: "ServerScanner"):
            self.scanner = scanner
            self.transport = None
        
        def connection_made(self, transport):
            self.transport = transport
            sock = transport.get_extra_info('socket')
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
                
                # Подписка на группу для получения Multicast ответов
                mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                
                # Отправка запроса: Broadcast + Multicast + Localhost
                request_data = MAGIC_REQUEST.encode()
                for port in range(DISCOVERY_PORT, DISCOVERY_PORT + 10):
                    self.transport.sendto(request_data, ('255.255.255.255', port))
                    self.transport.sendto(request_data, (MULTICAST_GROUP, port))
                    self.transport.sendto(request_data, ('127.0.0.1', port))
            except Exception as e:
                logger.debug(f"Scanner socket setup error: {e}")
        
        def datagram_received(self, data: bytes, addr):
            try:
                if len(data) > MAX_PACKET_SIZE:
                    return
                
                info = json.loads(data.decode('utf-8'))
                
                if info.get("_sig") != PROTOCOL_SIG:
                    return
                
                self.scanner.add_server(info.get("uid"), addr[0], info)
            
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                pass
            except Exception as e:
                logger.debug(f"Scan parse error: {e}")
    
    async def scan(self, timeout: float = 2.0):
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
    
    def add_server(self, uid: str, ip: str, info: dict):
        if uid not in self.found_servers:
            entry = ServerEntry.create(uid, info)
            entry += ip
            self.found_servers[uid] = entry
            self.server_found.emit(entry.pack())
            return
        
        entry = self.found_servers.get(uid)
        old_best = entry.get_best_address()
        entry += ip
        
        if entry.get_best_address() != old_best:
            self.server_found.emit(entry.pack())
