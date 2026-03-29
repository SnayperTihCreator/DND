import asyncio
import logging
from typing import TYPE_CHECKING

from CommonTools.components import BaseResourceManager

if TYPE_CHECKING:
    from .server_socket import AsyncServerBridge

logger = logging.getLogger(__name__)


class ServerResourceManager(BaseResourceManager):
    def __init__(self, socket: "AsyncServerBridge"):
        super().__init__(socket.assets)
        self.socket = socket
        
        self.socket.file_loaded.connect(self.resolve_file)
    
    def _on_file_missing(self, filename: str):
        logger.warning(f"Серверу потребовался ресурс {filename}, но его нет. Ждем загрузки...")
        asyncio.create_task(self._timeout_missing_file(filename, 30))
    
    async def _timeout_missing_file(self, filename: str, timeout: float):
        await asyncio.sleep(timeout)
        if filename in self._tasks:
            logger.error(f"Таймаут ожидания загрузки файла {filename} на сервере.")
            self.resolve_file(filename, success=False)  # Отменяем коллбеки
