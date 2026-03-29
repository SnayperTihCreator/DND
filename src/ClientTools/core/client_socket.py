import asyncio
import hashlib
import logging
import shutil
from typing import Optional

from pathlib import Path
import websockets
from attrs import define
from psygnal import Signal
from websockets import ClientConnection

from .transfer_manager import FileTransferManager
from .resource_manager import ClientResourceManager
from CommonTools.messages import *
from CommonTools.core import ClientData
from CommonTools.components import RouterDescriptor

logger = logging.getLogger(__name__)


@define
class ServerInfo:
    ip: Optional[str] = None
    ws_port: Optional[int] = None
    http_port: Optional[int] = None
    
    @property
    def is_valid(self) -> bool:
        return bool(self.http_port and self.ip)
    
    def url_http(self, extra=""):
        return "http://{ip}:{port}{extra}".format(ip=self.ip, port=self.http_port, extra=extra)
    
    def url_ws(self, extra=""):
        return "ws://{ip}:{port}{extra}".format(ip=self.ip, port=self.ws_port, extra=extra)


class AsyncClientBridge:
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
        
        self.server_info = ServerInfo()
        self.server_info.ws_port = 8765
        
        self.me = ClientData(uid="temp")
        logger.info("AsyncClientBridge initialized. Cache folder: %s", self.assets)
    
    def get_me(self) -> ClientData:
        return self.me
    
    def _on_transfer_failed(self, filename: str, error: str):
        self.error_occurred.emit(f"Transfer error for {filename}: {error}")
    
    def connect_server(self, ip, ws_port):
        self.server_info.ip = ip
        self.server_info.ws_port = ws_port
        uri = self.server_info.url_ws()
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
    
    def loadTo(self, path: str):
        sha256hash = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256hash.update(chunk)
        filename = f"{sha256hash.hexdigest()[:16]}{Path(path).suffix}"
        path2 = self.assets / filename
        if not path2.exists():
            shutil.copy(path, path2)
        return filename, path2
    
    @router_system.handler(SystemActionType.INFO)
    async def _on_handle_info_server(self, _, msg: SystemServerInfo):
        self.me.uid = msg.uid
        self.server_info.http_port = msg.http_port
        logger.info("Received server configuration: HTTP port %s", self.server_info.http_port)
        logger.info("Connected. My UID is: %s", self.me.uid)
    
    @router_system.handler(SystemActionType.RESOURCE_AVAILABLE)
    async def _on_handle_resources_server(self, _, msg: SystemResourceAvailable):
        url = self.server_info.url_http(f"/static/{msg.filename}")
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
        if not self.server_info.is_valid:
            msg = "Cannot upload: server connection details are not available."
            logger.error(msg)
            self.error_occurred.emit(msg)
            return None
        
        url = self.server_info.url_http("/upload")
        return await self.transfer.upload_file(local_path, url, self.me.uid)
