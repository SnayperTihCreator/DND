import asyncio
import logging

from psygnal import Signal

from ClientTools.core import AsyncClientBridge
from CommonTools.core import ClientData, ProxyAdapterSocket
from CommonTools.messages import BaseMessage, BaseSystemMessage, ProxyClientConnect, ProxyClientDisconnect, ProxyTunnel

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# TODO Дописать удаленку


class AsyncServerRemote(AsyncClientBridge):
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    server_started = Signal(list, int, int)
    message_handled = Signal(str, object)
    message_received = Signal(str, object)
    
    file_loaded = Signal(str)
    
    def __init__(self, token, assets="./.cache"):
        super().__init__(assets)
        self.server_info.ip, self.master_token = token.split("|")
        self.clients = {}
        self.me = ClientData("SERVER")
    
    def set_access(self, allow: bool):
        # TODO Я хз возможно нужно сразу ставить на открытие
        pass
    
    def loadTo(self, path: str):
        # TODO Реалтзовать загрузку
        pass
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            if uid == uid_answer: continue
            client.send(msg)
    
    def answer(self, uid: str, msg: BaseMessage):
        if uid in self.clients:
            self.clients[uid].send(msg)
    
    def send(self, msg: BaseMessage):
        for client in self.clients.values():
            client.send(msg)
    
    async def _process_message(self, message_str: str):
        try:
            msg = BaseMessage.from_str(message_str)
            
            if isinstance(msg, BaseSystemMessage):
                await self.router_system("", msg)
                return
            
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
                self.message_received.emit(msg.uid, msg.msg.to_str())
                return
            
            logger.debug("Passing message to main window handler: %s", message_str)
            self.message_handled.emit(self.me.uid, msg)
            self.message_received.emit(self.me.uid, message_str)
        
        except Exception:
            logger.exception("Error processing message: %s", message_str)
    
    async def proxy_send(self, msg: BaseMessage, uid: str):
        logger.warning("Sending proxy message %s: %s", msg, uid)
        proxy = ProxyTunnel(uid=uid, msg=msg)
        await self.asend(proxy)
    
    def connect_server(self, ip, port: int):
        self.server_info.ip = ip
        self.server_info.ws_port = port
        url = self.server_info.url_ws(f"/{self.master_token}")
        asyncio.create_task(self._connect_async(url))
    
    def start_server(self):
        self.connect_server(self.server_info.ip, self.server_info.ws_port)
    
    def stop_server(self):
        pass
