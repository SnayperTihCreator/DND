import asyncio
import logging
from typing import TYPE_CHECKING

from CommonTools.components import BaseResourceManager

if TYPE_CHECKING:
    from .client_socket import AsyncClientBridge

logger = logging.getLogger(__name__)


class ClientResourceManager(BaseResourceManager):
    def __init__(self, socket: 'AsyncClientBridge'):
        super().__init__(socket.cache_folder)
        self.socket = socket
        
        self.socket.transfer.file_downloaded.connect(lambda path, _: self.resolve_file(path))
        self.socket.transfer.transfer_failed.connect(lambda path, _: self.resolve_file(path, False))
    
    def _on_file_missing(self, filename: str):
        if self.socket.transfer.is_download(filename):
            return
        
        logger.info(f"Ресурс {filename} не найден. Запрашиваю скачивание.")
        asyncio.create_task(self._download(filename))
    
    async def _download(self, filename: str):
        if not self.socket.server_ip or self.socket.me.uid == "temp":
            self.resolve_file(filename, success=False)
            return
        
        url = f"http://{self.socket.server_ip}:{self.socket.server_http_port}/static/{filename}"
        await self.socket.transfer.download_file(url, self.folder / filename, self.socket.me.uid)
