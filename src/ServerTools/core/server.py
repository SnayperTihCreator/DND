import asyncio
import logging
from pathlib import Path

from attrs import define, field
from psygnal import set_async_backend

from CommonTools.messages import BaseMessage, ProxyClientConnect, ProxyClientDisconnect, ProxyTunnel
from CommonTools.components import RouterDescriptor
from .server_socket import AsyncServerBridge

logger = logging.getLogger(__name__)


@define(hash=True)
class Server:
    router = RouterDescriptor()
    
    master_token: str
    server: AsyncServerBridge = field(init=False, repr=False, hash=False)
    
    def __attrs_post_init__(self):
        self.server = AsyncServerBridge(Path("./.cache/remote"), self.master_token, True)
        self.server.client_connected.connect(self._handle_connect)
        self.server.client_disconnected.connect(self._handle_disconnect)
        
    def _handle_connect(self, uid):
        self.server.get_me().send(ProxyClientConnect(uid=uid))
        
    def _handle_disconnect(self, uid):
        self.server.get_me().send(ProxyClientDisconnect(uid=uid))
    
    def start_services(self):
        asyncio.create_task(self._start())
        
    def stop_services(self):
        self.server.stop_server()
    
    async def _start(self):
        backend = set_async_backend("asyncio")
        
        await backend.running.wait()
        self.server.message_handled.connect(self._handle_message)
        self.server.start_server()
    
    async def _handle_message(self, uid: str, msg: BaseMessage):
        logger.info("Proxy processing msg from %s: %s", uid, msg)
        self.server.get_me().send(ProxyTunnel(uid=uid, msg=msg))
