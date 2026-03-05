import asyncio
import socket
import uuid
from pathlib import Path
import logging

import websockets
from aiohttp import web
from psygnal import Signal

from CommonTools.core import ClientData, SocketAdapter
from CommonTools.core import MasterBeacon
from CommonTools.messages import *


logger = logging.getLogger(__name__)


class AsyncServerBridge:
    message_received_uid = Signal(str, str)
    message_received = Signal(str)
    
    client_connected = Signal(str)
    client_disconnected = Signal(str)
    
    server_started = Signal(list, int, int)
    server_error = Signal(str)
    
    def __init__(self, assets="./.cache"):
        self.clients = {}
        self.assets_folder = Path(assets)
        self.assets_folder.mkdir(parents=True, exist_ok=True)
        
        self.ws_port = 8765
        self.http_port = 8080
        self.available_ips = self._get_all_ips()
        
        self.is_public = False
        self.beacon = MasterBeacon()
        
        self._ws_server = None
        self._http_runner = None
    
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
                self.available_ips, self.ws_port, self.http_port
            ))
        else:
            self.beacon.stop()
    
    async def _start_async_services(self):
        try:
            self._ws_server = await websockets.serve(self._ws_handler, "0.0.0.0", self.ws_port)
            
            app = web.Application()
            app.router.add_static('/static/', path=self.assets_folder, name='static')
            app.router.add_post('/upload', self._handle_upload)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            for port in range(8080, 8100):
                try:
                    site = web.TCPSite(runner, "0.0.0.0", port)
                    await site.start()
                    self.http_port = port
                    self._http_runner = runner
                    break
                except OSError:
                    continue
            else:
                raise RuntimeError("No free HTTP ports")
            
            logger.info(f"Сервер работает: WS {self.ws_port}, HTTP {self.http_port}")
            self.server_started.emit(self.available_ips, self.ws_port, self.http_port)
        except Exception as e:
            logger.error(f"Ошибка сервера: {e}")
            self.server_error.emit(str(e))
    
    async def _ws_handler(self, websocket):
        if not self.is_public:
            await websocket.close(1008, "Table closed")
            return
        
        uid = uuid.uuid4().hex
        adapter = SocketAdapter(websocket)
        client_data = ClientData(uid=uid, socket=adapter)
        self.clients[uid] = client_data
        
        self.client_connected.emit(uid)
        self.answer(uid, SystemServerInfo(http_port=self.http_port, table_name="TestDND"))
        self.answer(uid, ClientConnect(uid=uid))
        
        try:
            async for message in websocket:
                self._process_message(uid, message)
        except Exception:
            pass
        finally:
            if uid in self.clients:
                del self.clients[uid]
            self.client_disconnected.emit(uid)
    
    def _process_message(self, uid, message_str):
        """ Твоя старая логика, перенесенная сюда """
        try:
            msg = BaseMessage.from_str(message_str)
            if msg.type == ClientActionType.START_PLAYER:
                if uid in self.clients:
                    self.clients[uid].name = msg.name
                    self.clients[uid].cls = msg.cls
                    self.clients[uid].is_playing = True
            
            self.message_received_uid.emit(uid, message_str)
            self.message_received.emit(message_str)
        except Exception:
            pass
    
    async def _handle_upload(self, request):
        reader = await request.multipart()
        field = await reader.next()
        if field.name != 'file': return web.Response(status=400)
        
        filename = f"{uuid.uuid4().hex}{Path(field.filename).suffix}"
        path = self.assets_folder / filename
        with open(path, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk: break
                f.write(chunk)
        
        return web.json_response({'url': self.get_file_url(filename)})
    
    def get_file_url(self, filename):
        best_ip = self.available_ips[0]
        return f"http://{best_ip}:{self.http_port}/static/{filename}"
    
    def broadcast(self, msg: BaseMessage, uid_answer=None):
        for uid, client in self.clients.items():
            if uid == uid_answer: continue
            client.send_msg(msg)
    
    def answer(self, uid: str, msg: BaseMessage):
        if uid in self.clients:
            self.clients[uid].send_msg(msg)
    
    def send(self, msg: BaseMessage):
        for client in self.clients.values():
            client.send_msg(msg)
    
    def send_image(self, *args, **kwargs):
        pass
    
    def answer_image(self, *args, **kwargs):
        pass
