import logging
from typing import Protocol

from attrs import define, field

from CommonTools.core import ClientData, SenderAdapterSocket
from CommonTools.messages import BaseMessage, ProxyActionType

logger = logging.getLogger(__name__)


class ServerTableProtocol(Protocol):
    async def __prepare_message__(self, uid: str, msg: BaseMessage): ...
    
    def answer(self, uid: str, msg: BaseMessage): ...
    
    def set_access(self, allow: bool): ...


@define
class MasterProxyHandler:
    server: ServerTableProtocol
    token: str
    no_master: bool = field(default=False)
    _data: ClientData = field(default=None)
    
    @property
    def isBusy(self) -> bool:
        if self.no_master:
            return True
        return self._data is not None and self._data.isAlive
    
    def is_token(self, token: str) -> bool:
        if self.no_master or not self.token:
            return False
        return self.token == token
    
    def attach(self, token: str, adapter: SenderAdapterSocket, uid: str):
        if self.no_master:
            return False
        
        if token and (self.token == token) and not self.isBusy:
            self._data = ClientData(uid, "MASTER", "MASTER", adapter)
            self._data.is_playing = True
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
        if msg.type == ProxyActionType.TUNNEL_DATA:
            await self.server.__prepare_message__(msg.uid, msg.msg)
            self.server.answer(msg.uid, msg.msg)
        
        logger.info("Не обработанное сообщение: %s - %s", msg.type, msg)
    
    @property
    def uid(self) -> str | None:
        if self._data:
            return self._data.uid
        return None
