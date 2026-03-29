import asyncio
import shutil
import socket
import uuid
from pathlib import Path
import logging
import hashlib
from typing import Optional

import websockets
from aiohttp import web
from attrs import define
from psygnal import Signal
import aiofiles

from CommonTools.core import ClientData, SocketAdapter, MasterBeacon
from CommonTools.messages import *
from .resource_manager import ServerResourceManager

logger = logging.getLogger(__name__)


@define
class ServerInfo:
    http_port: Optional[int] = None
    ws_port: Optional[int] = None


class AsyncServerBridge:
    message_received = Signal(str)
    message_handled = Signal(str, object)
    
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    server_started = Signal(list, int, int)
    error_occurred = Signal(str)
    
    file_loaded = Signal(str)
    
    def __init__(self, assets="./.cache", master_token="", no_master: bool = False):
        self.clients = {}
        self.assets = Path(assets)
        self.assets.mkdir(parents=True, exist_ok=True)
        
        self.serve_info = ServerInfo(8080, 8765)
        self.available_ips = self._get_all_ips()
        
        self.is_public = False
        self.beacon = MasterBeacon()
        
        self._ws_server = None
        self._http_runner = None
        self.manager = ServerResourceManager(self)
        self.master_token = master_token
        self.master_cd: ClientData = ClientData("")
        self.no_master = no_master
    
    @staticmethod
    def get_me():
        return ClientData("")
    
    @staticmethod
    def _get_all_ips():
        ip_list = []
        try:
            hostname = socket.gethostname()
            _, _, ips = socket.gethostbyname_ex(hostname)
            for ip in ips:
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    ip_list.append(ip)
        except:
            pass
        if not ip_list: ip_list.append("127.0.0.1")
        return ip_list
    
    def start_server(self):
        logger.info("Запуск AsyncServerBridge...")
        asyncio.create_task(self._start_async_services())
        return True
    
    def stop_server(self):
        self.beacon.stop()
        if self._ws_server: self._ws_server.close()
        if self._http_runner: asyncio.create_task(self._http_runner.cleanup())
        for client in self.clients.values():
            client.socket.close()
    
    def set_access(self, allow: bool):
        self.is_public = allow
        if allow:
            asyncio.create_task(self.beacon.start(
                self.available_ips, self.serve_info.ws_port, self.serve_info.http_port
            ))
        else:
            self.beacon.stop()
    
    async def _start_async_services(self):
        try:
            await self._start_async_ws()
            await self._start_async_http()
            logger.info(f"Сервер работает: WS {self.serve_info.ws_port}, HTTP {self.serve_info.http_port}")
            self.server_started.emit(self.available_ips, self.serve_info.ws_port, self.serve_info.http_port)
        except Exception as e:
            logger.error(f"Ошибка сервера: {e}")
            self.error_occurred.emit(str(e))
    
    async def _start_async_ws(self):
        self._ws_server = await websockets.serve(self._ws_handler, "0.0.0.0", self.serve_info.ws_port)
    
    async def _start_async_http(self):
        app = web.Application()
        app.router.add_get("/static/{filename}", self._handle_download)
        app.router.add_post('/upload', self._handle_upload)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        for port in range(8080, 8100):
            try:
                site = web.TCPSite(runner, "0.0.0.0", port)
                await site.start()
                self.serve_info.http_port = port
                self._http_runner = runner
                break
            except OSError:
                continue
        else:
            raise RuntimeError("No free HTTP ports")
    
    async def _ws_handler(self, websocket):
        path = websocket.request.path.strip("/")
        is_master = (path == self.master_token and self.no_master)
        
        if not self.is_public and not is_master:
            await websocket.close(1008, "Table closed")
            return
        
        uid = uuid.uuid4().hex
        adapter = SocketAdapter(websocket)
        client_data = ClientData(uid=uid, socket=adapter)
        
        if is_master:
            self.master_cd = client_data
            self.master_cd.is_playing = True
            self.master_cd.name = "MASTER"
            self.master_cd.cls = "MASTER"
            self.set_access(True)
        else:
            self.clients[uid] = client_data
            self.client_connected.emit(uid)
        
        self.answer(uid, SystemServerInfo(http_port=self.serve_info.http_port, table_name="TestDND", uid=uid))
        
        try:
            async for message in websocket:
                if is_master:
                    await self._process_message_master(uid, message)
                else:
                    await self._process_message(uid, message)
        except Exception:
            pass
        finally:
            if uid in self.clients:
                del self.clients[uid]
            self.client_disconnected.emit(uid)
            if is_master:
                self.set_access(False)
    
    async def _process_message_master(self, uid: str, message_str: str):
        try:
            msg = BaseMessage.from_str(message_str)
            logger.debug("Sender msg %s: %s", uid, msg)
        except Exception:
            pass
    
    async def _process_message(self, uid, message_str):
        """ Твоя старая логика, перенесенная сюда """
        try:
            msg = BaseMessage.from_str(message_str)
            if msg.type == ClientActionType.START_PLAYER:
                if uid in self.clients:
                    self.clients[uid].name = msg.name
                    self.clients[uid].cls = msg.cls
                    self.clients[uid].is_playing = True
            
            self.message_handled.emit(uid, msg)
            self.message_received.emit(message_str)
        except Exception:
            pass
    
    async def _handle_download(self, request: web.Request):
        uid = request.query.get("uid") or request.headers.get("X-User-ID")
        if not uid:
            return web.json_response({"error": "Missing UID"}, status=401)
        
        cd = self.clients.get(uid) or self.master_cd.uid
        if not cd or not cd.is_playing:
            return web.json_response({"error": "Forbidden: You are not an active player"}, status=403)
        
        filename = request.match_info.get("filename")
        if not filename:
            return web.json_response({"error": "Missing filename"}, status=400)
        
        filename = Path(filename).name
        path = self.assets / filename
        
        if not path.exists() or not path.is_file():
            return web.json_response({"error": "File not found"}, status=404)
        
        return web.FileResponse(path)
    
    async def _handle_upload(self, request: web.Request):
        uid = request.query.get("uid") or request.headers.get("X-User-ID")
        if not uid:
            return web.json_response({"error": "Missing UID"}, status=401)
        
        cd = self.clients.get(uid) or self.master_cd.uid
        if not cd or not cd.is_playing:
            return web.json_response({"error": "Forbidden: You are not an active player"}, status=403)
        
        reader = await request.multipart()
        field = await reader.next()
        
        filename = Path(field.filename).name
        path = self.assets / filename
        
        async with aiofiles.open(path, 'wb') as file:
            while True:
                chunk = await field.read_chunk()
                if not chunk: break
                await file.write(chunk)
        
        self.file_loaded.emit(field.filename)
        return web.json_response({'url': filename})
    
    def loadTo(self, path: str):
        sha256hash = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256hash.update(chunk)
        filename = f"{sha256hash.hexdigest()[:16]}{Path(path).suffix}"
        path2 = self.assets / filename
        if not path2.exists():
            shutil.copy(path, path2)
        return filename
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            if uid == uid_answer: continue
            client.send(msg)
    
    def answer(self, uid: str, msg: BaseMessage):
        if uid in self.clients:
            self.clients[uid].send(msg)
    
    def send(self, msg: BaseMessage):
        for client in self.clients.values():
            client.send(msg)
