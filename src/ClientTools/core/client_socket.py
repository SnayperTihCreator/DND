import asyncio
import logging
from pathlib import Path
from typing import Optional

import websockets
from psygnal import Signal
from websockets import ClientConnection

from CommonTools.components import RouterDescriptor
from CommonTools.core import ClientData, ResourceLoaderMixin, NetworkConfig
from network.messages import *
from .resource_manager import ClientResourceManager
from .transfer_manager import FileTransferManager

logger = logging.getLogger(__name__)


class AsyncClientBridge(ResourceLoaderMixin):
    router_system = RouterDescriptor()
    
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    
    message_received = Signal(str)
    message_handled = Signal(object)
    
    def __init__(self, assets="./.cache/client"):
        self.socket: Optional[ClientConnection] = None
        self.transfer = FileTransferManager()
        self.transfer.transfer_failed.connect(self._on_transfer_failed)
        self.assets = Path(assets)
        self.assets.mkdir(parents=True, exist_ok=True)
        self.manager = ClientResourceManager(self)
        
        self.config = NetworkConfig(None, 8765, 8080)
        
        self.me = ClientData(uid="temp")
        logger.info("AsyncClientBridge initialized. Cache folder: %s", self.assets)
    
    def get_me(self) -> ClientData:
        return self.me
    
    def _on_transfer_failed(self, filename: str, error: str):
        self.error_occurred.emit(f"Transfer error for {filename}: {error}")
    
    def connect_server(self, ip, ws_port, extra=""):
        self.config.ip, self.config.ws_port = ip, ws_port
        uri = self.config.ws(extra)
        asyncio.create_task(self._connect_async(uri))
    
    def disconnect_server(self):
        if self.socket:
            logger.info("Requesting disconnection from server.")
            asyncio.create_task(self.socket.close())
    
    async def _connect_async(self, uri: str):
        logger.info("Connecting to %s...", uri)
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20, open_timeout=10) as websocket:
                self.socket = websocket
                logger.info("WebSocket connection established to %s", uri)
                self.connected.emit()
                await self._listen_for_messages()
                
        except Exception as e:
            logger.error("Connection failed to %s: %s", uri, e)
            self.error_occurred.emit(f"Connection error: {e}")
        finally:
            self.socket = None
            logger.info("WebSocket connection to %s is closed.", uri)
            self.disconnected.emit()
    
    async def _listen_for_messages(self):
        if not self.socket:
            return
        logger.info("Listening for incoming messages...")
        async for message in self.socket:
            logger.info("Received message: %s", message)
            await self._process_message(message)
    
    async def _process_message(self, message_str: str):
        try:
            msg = BaseMessage.from_str(message_str)
            
            if isinstance(msg, BaseSystemMessage):
                await self.router_system("", msg)
                return
            
            logger.debug("Passing message to main window handler: %s", message_str)
            self.message_handled.emit(msg)
            self.message_received.emit(message_str)
        
        except Exception:
            logger.exception("Error processing message: %s", message_str)
    
    @router_system.handler(SystemActionType.INFO)
    async def _on_handle_info_server(self, _, msg: SystemServerInfo):
        self.me.uid, self.config.http_port = msg.uid, msg.http_port
        logger.info("Received server configuration: HTTP port %s", self.config.http_port)
        logger.info("Connected. My UID is: %s", self.me.uid)
    
    @router_system.handler(SystemActionType.RESOURCE_AVAILABLE)
    async def _on_handle_resources_server(self, _, msg: SystemResourceAvailable):
        url = self.config.http(f"/static/{msg.filename}")
        local_path = self.assets / Path(msg.filename)
        logger.info("File URL detected in message. Scheduling download for %s", local_path)
        await self.transfer.download_file(url, local_path, self.me.uid)
    
    def send(self, msg: BaseMessage):
        asyncio.create_task(self.asend(msg))
    
    async def asend(self, msg: BaseMessage):
        if self.socket:
            logger.debug("Sending message: %s", msg)
            await self.socket.send(msg.to_str())
    
    async def upload_file(self, local_path: Path) -> Optional[str]:
        """
        Prepares the upload URL and delegates the file upload to the FileTransferManager.
        """
        if not self.config.is_valid:
            msg = "Cannot upload: server connection details are not available."
            logger.error(msg)
            self.error_occurred.emit(msg)
            return None
        
        url = self.config.http("/upload")
        return await self.transfer.upload_file(local_path, url, self.me.uid)
