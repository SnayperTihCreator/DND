import asyncio
import logging
from typing import Optional

import json5
from pathlib import Path
import websockets
import aiohttp
from psygnal import Signal

from CommonTools.messages import *
from CommonTools.core import ClientData

logger = logging.getLogger(__name__)


class Downloader:
    download_progress = Signal(str, int)
    file_downloaded = Signal(str, Path)
    
    async def download_file(self, url: str, local_path: Path):
        file_id = local_path.name
        logger.info("Starting download: %s -> %s", url, local_path)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(local_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = int(downloaded / total_size * 100)
                                self.download_progress.emit(file_id, percent)
            
            self.file_downloaded.emit(file_id, local_path)
            logger.info("File downloaded successfully: %s", local_path)
        
        except Exception:
            logger.exception("Download failed for URL: %s", url)


class AsyncClientBridge:
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, cache_folder="./.cache/client"):
        self.socket = None
        self.downloader = Downloader()
        self.cache_folder = Path(cache_folder)
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        
        self.server_ip: Optional[str] = None
        self.server_http_port: Optional[int] = None
        
        self.me = ClientData(uid="temp")
        logger.info("AsyncClientBridge initialized. Cache folder: %s", self.cache_folder)
    
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
            self._process_message(message)
    
    def _process_message(self, message_str: str):
        logger.debug("Processing incoming message: %s", message_str)
        try:
            msg = BaseMessage.from_str(message_str)
            
            if isinstance(msg, BaseSystemMessage):
                if msg.type == SystemActionType.INFO:
                    self.server_http_port = msg.http_port
                    logger.info("Received server configuration: HTTP port %s", self.server_http_port)
                return
            
            if hasattr(msg, 'url') and msg.url:
                filename = msg.name + Path(msg.url).suffix
                local_path = self.cache_folder / filename
                logger.info("File URL detected in message. Scheduling download for %s", local_path)
                asyncio.create_task(self.downloader.download_file(msg.url, local_path))
            
            if msg.type == ClientActionType.CONNECT:
                self.me.uid = msg.uid
                logger.info("Connected. My UID is: %s", msg.uid)
            else:
                logger.debug("Passing message to main window handler: %s", message_str)
                self.message_received.emit(message_str)
        
        except Exception:
            logger.exception("Error processing message: %s", message_str)
            self.message_received.emit(message_str)
    
    def send_msg(self, msg_obj: BaseMessage):
        if self.socket:
            text = json5.dumps(msg_obj.to_dict(), ensure_ascii=False)
            logger.debug("Sending message: %s", text)
            asyncio.create_task(self.socket.send(text))
    
    async def upload_file(self, local_path: Path) -> Optional[str]:
        if not self.server_ip or not self.server_http_port:
            msg = "Cannot upload: server IP or HTTP port is not set."
            logger.error(msg)
            self.error_occurred.emit(msg)
            return None
        
        url = f"http://{self.server_ip}:{self.server_http_port}/upload"
        logger.info("Attempting to upload file %s to %s", local_path, url)
        
        data = aiohttp.FormData()
        data.add_field('file', open(local_path, 'rb'), filename=local_path.name)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info("File uploaded successfully: %s -> %s", local_path.name, result.get('url'))
                    return result.get('url')
        except Exception as e:
            logger.exception("Upload failed for file: %s", local_path)
            self.error_occurred.emit(f"Upload failed: {e}")
            return None
