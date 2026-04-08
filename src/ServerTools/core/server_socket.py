import asyncio
import logging
import uuid
from pathlib import Path

from psygnal import Signal
from websockets import ServerConnection, ConnectionClosedError

from CommonTools.core import ClientData, SocketAdapter, MasterBeacon, NetworkConfig, ResourceLoaderMixin
from CommonTools.messages import *
from .proxy import MasterProxyHandler
from .resource_manager import ServerResourceManager
from .server_http import ServerHttp
from .server_ws import ServerWS

logger = logging.getLogger(__name__)


class AsyncServerBridge(ResourceLoaderMixin):
    message_received = Signal(str)
    message_handled = Signal(str, object)
    
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    server_started = Signal(int, int)
    error_occurred = Signal(str)
    
    file_loaded = Signal(str)
    
    def __init__(self, assets="./.cache", token="", no_master: bool = False):
        self.clients = {}
        self.assets = Path(assets)
        self.assets.mkdir(parents=True, exist_ok=True)
        
        self.config = self.serve_info = NetworkConfig(None, 8080, 8765)
        
        self.proxy_handler = MasterProxyHandler(self, token, no_master)
        self.server_ws = ServerWS(self)
        
        self.service_http = ServerHttp(self)
        self.manager = ServerResourceManager(self)
        
        self.beacon = MasterBeacon()
    
    def get_me(self):
        return self.proxy_handler.master
    
    def start_server(self):
        logger.info("Запуск AsyncServerBridge...")
        asyncio.create_task(self._start_async_services())
        return True
    
    def stop_server(self):
        self.beacon.stop()
        asyncio.create_task(self.server_ws.stop())
        asyncio.create_task(self.service_http.stop())
        for client in self.clients.values():
            client.socket.close()
    
    def set_access(self, allow: bool):
        if allow:
            asyncio.create_task(self.beacon.start(self.serve_info.ws_port))
        else:
            self.beacon.stop()
    
    async def _start_async_services(self):
        try:
            
            self.config.ws_port = await self.server_ws.start()
            self.config.http_port = await self.service_http.start()
            logger.info(f"Сервер работает: WS {self.serve_info.ws_port}, HTTP {self.serve_info.http_port}")
            self.server_started.emit(self.serve_info.ws_port, self.serve_info.http_port)
        
        except Exception as e:
            logger.error(f"Ошибка сервера: {e}")
            self.error_occurred.emit(str(e))
    
    async def handle_websocket(self, websocket):
        await self._ws_handler(websocket)
    
    async def _ws_handler(self, websocket: ServerConnection):
        path = websocket.request.path.strip("/")
        uid = uuid.uuid4().hex
        adapter = SocketAdapter(websocket)
        
        is_master = self.proxy_handler.attach(path, adapter, uid)
        
        if not is_master:
            if self.proxy_handler.is_token(path):
                logger.warning(f"Rejecting client {uid}: Master slot occupied")
                await websocket.close(1008, "Master slot occupied")
                return
            
            if not self.beacon.is_public:
                logger.warning(f"Rejecting client {uid}: Table is not public yet!")
                await websocket.close(1008, "Table closed")
                return
        
        if not is_master:
            logger.info(f"Add client {uid} to table")
            client_data = ClientData(uid=uid, socket=adapter)
            self.clients[uid] = client_data
            self.client_connected.emit(uid)
        
        self.answer(uid, SystemServerInfo(
            http_port=self.serve_info.http_port,
            table_name="TestDND",
            uid=uid
        ))
        
        try:
            async for message in websocket:
                msg = BaseMessage.from_str(message)
                if is_master:
                    await self.proxy_handler.process_message(uid, msg)
                else:
                    await self._process_message(uid, msg)
        except Exception:
            logger.exception("Error during WS session", exc_info=True)
            
        except ConnectionClosedError:
            pass
        finally:
            if uid in self.clients:
                del self.clients[uid]
                self.client_disconnected.emit(uid)
            self.proxy_handler.detach(uid)
    
    async def _process_message(self, uid, msg: BaseMessage):
        """ Твоя старая логика, перенесенная сюда """
        await self.__prepare_message__(uid, msg)
        self.message_handled.emit(uid, msg)
        self.message_received.emit(msg.to_str())
    
    async def __prepare_message__(self, uid: str, msg: BaseMessage):
        if (msg.type == ClientActionType.START_PLAYER) and (uid in self.clients):
            self.clients[uid].name = msg.name
            self.clients[uid].cls = msg.cls
            self.clients[uid].is_playing = True
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            if uid == uid_answer: continue
            client.send(msg)
    
    def answer(self, uid: str, msg: BaseMessage):
        if uid in self.clients:
            self.clients[uid].send(msg)
            return True
        return False
    
    def send(self, msg: BaseMessage):
        for client in self.clients.values():
            client.send(msg)
