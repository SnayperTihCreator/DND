import asyncio
import logging
import sys
from contextvars import ContextVar
from typing import Optional

import websockets
import uuid

from ServerTools import *


class DnDServer:
    def __init__(self, tag_tolerance: str):
        self._tag_tolerance = tag_tolerance
        self.max_size = 50 * 1024 * 1024
        
        self.clients: dict[str, ClientContext] = {}
        self.master: Optional[ClientContext] = None
        self._client_context = ContextVar("client-context")
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        self.logger = logging.getLogger("DndServer")
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
    
    def register(self, websocket: websockets.ClientConnection, uid: str) -> ClientContext:
        """Регистрация нового клиента"""
        self.clients[uid] = ClientContext(uid, websocket)
        self.logger.info(f"Add client <{uid}>. Total: {len(self.clients)}")
        return self.clients[uid]
    
    async def unregister(self, uid: str):
        """Удаление клиента и рассылка уведомлений"""
        
        if self.clients[uid]:
            if self.master and uid != self.master.uid and self.clients[uid].is_player:
                await self.broadcast(ClientRemovePlayer(uid=uid))
            
            if self.master and uid == self.master.uid:
                self.master = None
        
        if uid in self.clients:
            del self.clients[uid]
        
        self.logger.info(f"Remove player <{uid}>")
    
    async def handle_message(self, msg_raw: str):
        """Обработка входящего сообщения"""
        try:
            msg = BaseMessage.from_str(msg_raw)
            await self.handle_request(msg)
        except Exception as e:
            self.logger.error(f"JSON decode error: {e}")
    
    async def handle_request(self, msg: BaseMessage):
        """Обработка структурированного запроса"""
        match msg.type:
            case ClientActionType.START_PLAYER:
                await self._handle_client_start_player(msg)
            case ClientActionType.START_MASTER:
                await self._handle_client_start_master(msg)
            case MapActionType.LOAD_BACKGROUND:
                await self._handle_map_background(msg)
            case ImageActionType.NAME_REQUEST:
                await self._handle_image_data(msg)
            case ImageActionType(group="image"):
                await self._handle_image_broadcast(msg)
            case ClientActionType.MASTER_CONNECT_HAS:
                await self._handle_master_connect_has(msg)
            case MapActionType.ADD_TOKEN | MapActionType.REMOVE_TOKEN | MapActionType.MOVE_TOKEN | MapActionType.MAP_CHANGE_GRID_OFFSET:
                await self.broadcast(msg)
            case MapActionType.ADD_TOKEN2:
                await self._handle_add_token_uid(msg)
            case MapActionType.GET_BEGIN_LOAD if self.master is not None:
                await self.master.send_msg(msg)
            case MapActionType.GET_ALL_TOKEN if self.master is not None:
                await self.master.send_msg(msg)
            case MapActionType.MAP_CREATE | MapActionType.MAP_GRID_DATA | MapActionType.MAP_MOVE_MAP:
                await self.broadcast(msg, False)
            case MapActionType.PLAYER_FREEZE | ClientActionType.PLAYER_STOP:
                await self.clients[msg.uid].send_msg(msg)
            case _:
                self.logger.info(f"Unhandled message type: {msg.type}")
            
    async def _handle_add_token_uid(self, msg: MapAddToken2):
        await self.clients[msg.uid].send_msg(MapAddToken(name=msg.name, mime=msg.mime, pos=msg.pos))
    
    async def _handle_master_connect_has(self, msg: ClientMasterConnectHas):
        if self.master is not None:
            await self.answer(DoneCallback(uid_callback=msg.uid_callback))
        else:
            await self.answer(IgnoreCallback(uid_callback=msg.uid_callback))
    
    async def _handle_client_start_player(self, msg: ClientStartPlayer):
        """Обработка подключения игрока"""
        context: ClientContext = self._client_context.get()
        context.name = msg.name
        context.cls = msg.cls
        context.is_player = True
        
        await self.answer(ClientStartPlayer(name=msg.name, cls=msg.cls))
        await self.broadcast(ClientAddPlayer(name=msg.name, uid=context.uid, cls=msg.cls))
        
        # Отправка информации о других игроках
        for client in self.clients.values():
            if not client.is_master and client.uid != context.uid:
                await self.answer(ClientAddPlayer(name=client.name, uid=client.uid, cls=msg.cls))
        
        self.logger.info(f"Add player {msg.name}")
    
    async def _handle_client_start_master(self, msg: ClientStartMaster):
        """Обработка подключения мастера"""
        if self.master is not None:
            await self.answer(ErrorMessage(error="Мастер уже есть"))
            return
        
        if self._tag_tolerance != msg.tag:
            await self.answer(ErrorMessage(error="Неверный тег пропуска"))
            return
        
        context = self._client_context.get()
        context.is_master = True
        self.master = context
        
        await self.answer(ClientStartMaster(tag=""))
        
        # Отправка информации о существующих игроках
        for client in self.clients.values():
            if client.uid != context.uid:
                await self.answer(ClientAddPlayer(uid=client.uid, name=client.name, cls=client.cls))
        
        self.logger.info("Add master")
    
    async def _handle_map_background(self, msg: MapLoadBackground):
        """Обработка данных фоновой карты"""
        if msg.uid:
            await self.clients[msg.uid].send_msg(msg)
        else:
            await self.broadcast(msg, include_master=False)
    
    async def _handle_image_data(self, msg: ImageNameRequest):
        """Обработка данных изображения с указанием получателя"""
        await self.broadcast(msg)
    
    async def _handle_image_broadcast(self, msg: ImageMessage):
        """Обработка широковещательной передачи изображений"""
        if msg.uid:
            await self.clients[msg.uid].send_msg(msg)
        else:
            await self.broadcast(msg)
    
    async def broadcast(self, msg: BaseMessage, include_master: bool = True):
        """Широковещательная рассылка сообщения"""
        context = self._client_context.get()
        tasks = []
        
        for client in self.clients.values():
            if client.uid == context.uid or (client.is_master and not include_master):
                continue
            tasks.append(client.send_msg(msg))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def answer(self, msg: BaseMessage):
        """Отправка ответа текущему клиенту"""
        context = self._client_context.get()
        await context.send_msg(msg)
    
    async def handler(self, websocket: websockets.ClientConnection):
        """Основной обработчик соединения"""
        uid = uuid.uuid4().hex
        context = self.register(websocket, uid)
        token = self._client_context.set(context)
        
        try:
            await self.answer(ClientConnect(uid=uid))
            async for message in websocket:
                await self.handle_message(message)
        finally:
            await self.unregister(uid)
            self._client_context.reset(token)


async def main():
    """Точка входа приложения"""
    if len(sys.argv) < 2:
        print("Usage: python server_socket.py <tag_tolerance>")
        return
    
    server = DnDServer(sys.argv[1])
    host, port = "0.0.0.0", 8765
    
    server.logger.info(f"Starting server on {host}:{port}")
    async with websockets.serve(server.handler, host, port, max_size=server.max_size):
        await asyncio.Future()  # Бесконечное ожидание


if __name__ == "__main__":
    asyncio.run(main())
