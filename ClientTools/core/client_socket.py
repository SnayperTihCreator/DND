import asyncio
from typing import Optional

import json5
from pathlib import Path
from loguru import logger

import websockets
import aiohttp
from psygnal import Signal

from CommonTools.messages import *
from CommonTools.core import ClientData, SocketAdapter


class Downloader:
    download_progress = Signal(str, int)  # file_id, percent
    file_downloaded = Signal(str, Path)  # file_id, local_path
    
    async def download_file(self, url: str, local_path: Path):
        file_id = local_path.name
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
            logger.success(f"File downloaded: {local_path}")
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")


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
        
        # Данные самого клиента (можно использовать ClientData)
        self.me = ClientData(uid="temp")
    
    def connect_server(self, ip, port=8765):
        """Запускает задачу подключения"""
        self.server_ip = ip
        uri = f"ws://{ip}:{port}"
        asyncio.create_task(self._connect_async(uri))
    
    def disconnect_server(self):
        if self.socket:
            asyncio.create_task(self.socket.close())
    
    async def _connect_async(self, uri: str):
        logger.info(f"Connecting to {uri}...")
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20, open_timeout=10) as websocket:
                self.socket = websocket
                self.connected.emit()
                
                await self._listen_for_messages()
        
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
        finally:
            self.socket = None
            self.disconnected.emit()
    
    async def _listen_for_messages(self):
        """Бесконечно слушает сообщения от сервера"""
        async for message in self.socket:
            self._process_message(message)
    
    def _process_message(self, message_str: str):
        try:
            msg = BaseMessage.from_str(message_str)
            
            if isinstance(msg, BaseSystemMessage):
                match msg.type:
                    case SystemActionType.INFO:
                        self.server_http_port = msg.http_port
                        logger.success(f"Получена конфигурация сервера: HTTP порт {self.master_http_port}")
                        return
                return
            
            if hasattr(msg, 'url') and msg.url:
                filename = msg.name + Path(msg.url).suffix
                local_path = self.cache_folder / filename
                
                asyncio.create_task(self.downloader.download_file(msg.url, local_path))
            
            if msg.type == ClientActionType.CONNECT:
                self.me.uid = msg.uid
                logger.success(f"Connected. My UID is: {msg.uid}")
            else:
                self.message_received.emit(message_str)
        
        except Exception:
            self.message_received.emit(message_str)
    
    def send_msg(self, msg_obj: BaseMessage):
        """Отправляет сообщение серверу"""
        if self.socket:
            text = json5.dumps(msg_obj.to_dict(), ensure_ascii=False)
            asyncio.create_task(self.socket.send(text))
    
    async def upload_file(self, local_path: Path):
        if not self.server_ip:
            self.error_occurred.emit("Нет IP адреса сервера для загрузки.")
            return None
        
        url = f"http://{self.server_ip}:{self.server_http_port}/upload"
        
        data = aiohttp.FormData()
        data.add_field('file', open(local_path, 'rb'), filename=local_path.name)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result['url']
        except Exception as e:
            self.error_occurred.emit(f"Upload failed: {e}")
            return None
