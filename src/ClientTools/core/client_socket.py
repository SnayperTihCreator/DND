import asyncio
import logging
from typing import Optional

import json5
from pathlib import Path
import websockets
from psygnal import Signal

from .transfer_manager import FileTransferManager
from .resource_manager import ClientResourceManager
from CommonTools.messages import *
from CommonTools.core import ClientData
from CommonTools.components import RouterDescriptor

logger = logging.getLogger(__name__)


class AsyncClientBridge:
    router_system = RouterDescriptor()
    
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    
    message_received = Signal(str)
    message_handled = Signal(object)
    
    def __init__(self, cache_folder="./.cache/client"):
        self.socket = None
        self.transfer = FileTransferManager()
        self.transfer.transfer_failed.connect(self._on_transfer_failed)
        self.cache_folder = Path(cache_folder)
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        self.manager = ClientResourceManager(self)
        
        self.server_ip: Optional[str] = None
        self.server_http_port: Optional[int] = None
        
        self.me = ClientData(uid="temp")
        logger.info("AsyncClientBridge initialized. Cache folder: %s", self.cache_folder)
    
    def get_me(self) -> ClientData:
        return self.me
    
    def _on_transfer_failed(self, filename: str, error: str):
        self.error_occurred.emit(f"Transfer error for {filename}: {error}")
    
    def connect_server(self, ip, port=8765):
        self.server_ip = ip
        uri = f"ws://{ip}:{port}"
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
        self.me.uid = msg.uid
        self.server_http_port = msg.http_port
        logger.info("Received server configuration: HTTP port %s", self.server_http_port)
        logger.info("Connected. My UID is: %s", self.me.uid)
    
    @router_system.handler(SystemActionType.RESOURCE_AVAILABLE)
    async def _on_handle_resources_server(self, _, msg: SystemResourceAvailable):
        url = f"http://{self.server_ip}:{self.server_http_port}/static/{msg.filename}"
        local_path = self.cache_folder / Path(msg.filename)
        logger.info("File URL detected in message. Scheduling download for %s", local_path)
        await self.transfer.download_file(url, local_path, self.me.uid)
    
    def send_msg(self, msg_obj: BaseMessage):
        if self.socket:
            text = json5.dumps(msg_obj.to_dict(), ensure_ascii=False)
            logger.debug("Sending message: %s", text)
            asyncio.create_task(self.socket.send(text))
    
    async def upload_file(self, local_path: Path) -> Optional[str]:
        """
        Prepares the upload URL and delegates the file upload to the FileTransferManager.
        """
        if not self.server_ip or not self.server_http_port:
            msg = "Cannot upload: server connection details are not available."
            logger.error(msg)
            self.error_occurred.emit(msg)
            return None
        
        upload_url = f"http://{self.server_ip}:{self.server_http_port}/upload"
        return await self.transfer.upload_file(local_path, upload_url, self.me.uid)
