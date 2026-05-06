import asyncio
import logging
from pathlib import Path

from ClientTools.core import AsyncClientBridge
from CommonTools.components import RouterDescriptor
from CommonTools.core import ClientData, ProxyAdapterSocket, ResourceLoaderMixin
from network.messages import *
from ServerTools.core.resource_manager import ServerResourceManager
from psygnal import Signal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AsyncServerRemote(ResourceLoaderMixin):
    router = RouterDescriptor()
    
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    server_started = Signal(int, int)
    message_handled = Signal(str, object)
    message_received = Signal(str, object)
    
    error_occurred = Signal(str)
    file_loaded = Signal(str)
    
    def __init__(self, token: str, assets="./.cache"):
        self.clients: dict[str, ClientData] = {}
        self.bridge: AsyncClientBridge = AsyncClientBridge(assets)
        
        self.manager = ServerResourceManager(self)
        self.config.ip, self.master_token = token.split("|")
        self.master_token = self.master_token.strip()
    
    def get_me(self):
        return self.me
    
    @property
    def config(self):
        return self.bridge.config
    
    @property
    def me(self):
        return self.bridge.me
    
    @property
    def assets(self):
        return self.bridge.assets
    
    def start_server(self):
        self.bridge.message_received.connect(self._process_message)
        
        asyncio.create_task(self.connect_server(self.config.ip, self.config.ws_port))
    
    def stop_server(self):
        pass
    
    async def connect_server(self, ip: str, port: int):
        self.bridge.connect_server(ip, port, f"/{self.master_token}")
    
    async def _process_message(self, message: str):
        try:
            msg = BaseMessage.from_str(message)
            
            if isinstance(msg, ProxyClientConnect):
                adapter = ProxyAdapterSocket(None, msg.uid, self)
                self.clients[msg.uid] = ClientData(msg.uid, socket=adapter)
                self.client_connected.emit(msg.uid)
                return
            
            if isinstance(msg, ProxyClientDisconnect):
                if msg.uid in self.clients:
                    del self.clients[msg.uid]
                self.client_disconnected.emit(msg.uid)
                return
            
            if isinstance(msg, ProxyTunnel):
                if not isinstance(msg.msg, BaseMessage):
                    raise TypeError("msg must be BaseMessage")
                self.message_handled.emit(msg.uid, msg.msg)
                self.message_received.emit(msg.uid, message)
                return
            
            logger.debug("Passing message to main window handler: %s", message)
            self.message_handled.emit(self.me.uid, message)
            self.message_received.emit(self.me.uid, message)
        except Exception:
            logger.exception("Error processing message: %s", message)
    
    async def proxy_send(self, msg: BaseMessage, uid: str):
        logger.warning("Sending proxy message %s: %s", msg, uid)
        await self._asend(ProxyTunnel(uid=uid, msg=msg))
    
    async def _asend(self, msg: BaseMessage):
        if self.bridge.socket:
            await self.bridge.socket.send(msg.to_str())
    
    def _send(self, msg: BaseMessage):
        asyncio.create_task(self._asend(msg))
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            if uid == uid_answer: continue
            client.send(msg)
    
    def send(self, msg: BaseMessage):
        for client in self.clients.values():
            client.send(msg)
    
    def answer(self, uid: str, msg: BaseMessage):
        if uid in self.clients:
            self.clients[uid].send(msg)
    
    def set_access(self, allow: bool):
        self._send(ProxyOpenTable(open=allow))
    
    def loadTo(self, path: str | Path) -> str:
        super().loadTo(path)
        asyncio.create_task(self.bridge.upload_file(path))
