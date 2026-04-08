import logging
from typing import Protocol

from attrs import define, field

from CommonTools.components import RouterDescriptor
from CommonTools.core import ClientData, SenderAdapterSocket
from CommonTools.messages import BaseMessage, ProxyActionType, ProxyTunnel, ProxyOpenTable

logger = logging.getLogger(__name__)


class ServerTableProtocol(Protocol):
    async def __prepare_message__(self, uid: str, msg: BaseMessage): ...
    
    def answer(self, uid: str, msg: BaseMessage): ...
    
    def set_access(self, allow: bool): ...


@define(hash=True)
class MasterProxyHandler:
    router = RouterDescriptor()
    
    server: ServerTableProtocol = field(hash=False)
    token: str
    no_master: bool = field(default=False, hash=False)
    _data: ClientData = field(default=None, hash=False)
    
    def __attrs_post_init__(self):
        self.token = self.token.strip()
        
    @property
    def master(self):
        return self._data
    
    @property
    def isBusy(self) -> bool:
        return self._data is not None and self._data.isAlive
    
    def is_token(self, token: str) -> bool:
        if not self.token or not token:
            return False
        return self.token == token
    
    def attach(self, token: str, adapter: SenderAdapterSocket, uid: str):
        if not token or (self.token != token):
            return False
        
        if not self.isBusy:
            self._data = ClientData(uid, "MASTER", "MASTER", adapter)
            self._data.is_playing = True
            
            self.no_master = False
            
            logger.info(f"Master attached with UID: {uid}")
            return True
        
        return False
    
    def detach(self, uid):
        if self._data and (self._data.uid == uid):
            self.server.set_access(False)
            self._data = None
            return True
        return False
    
    async def process_message(self, uid: str, msg: BaseMessage):
        
        if await self.router(uid, msg):
            return
        
        logger.info("Не обработанное сообщение: %s - %s", msg.type, msg)
    
    @router.handler(ProxyActionType.TUNNEL_DATA)
    async def _handler_tunnel_data(self, uid: str, msg: ProxyTunnel):
        await self.server.__prepare_message__(msg.uid, msg.msg)
        self.server.answer(msg.uid, msg.msg)
        return True
        
    @router.handler(ProxyActionType.TABLE_SWITCH)
    async def _handler_table_switch(self, uid: str, msg: ProxyOpenTable):
        self.server.set_access(msg.open)
        return True
    
    @property
    def uid(self) -> str | None:
        if self._data:
            return self._data.uid
        return None
