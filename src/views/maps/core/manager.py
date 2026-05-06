from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItem
from psygnal import Signal

from network.mime import *
from ..tokens import BaseToken
from ..tokens.tokens import PlayerToken, SpawnPlayerToken, NPCToken, MobToken
from ..utils.data import CreateData
from ..utils.dialog_create_token import DialogCreateToken

if TYPE_CHECKING:
    from .map import Map, MoveSetting
    from .map_provider import MapProvider


class Manager:
    token_added = Signal(BaseToken)
    token_moved = Signal(TokenMime, QPointF)
    token_removed = Signal(TokenMime)
    token_map_moved = Signal(BaseToken, QPointF)
    
    def __init__(self, scene: Map, provider: MapProvider):
        self.scene = scene
        self.provider = provider
        self._tokens: dict[TokenMime, BaseToken] = {}
        self._names: defaultdict[str, int] = defaultdict(int)
    
    def update_size_tokens(self):
        for token in self._tokens.values():
            token.update_grid()
    
    def clear(self):
        for token in self._tokens.values():
            self.removeToken(token)
            
    def update_moved(self, setting: MoveSetting):
        for token in self._tokens.values():
            status = getattr(setting, token.ttype, False)
            token.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, status)
            token.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, status)
    
    def addToken(self, pos: QPointF, token: BaseToken):
        self._tokens[token.mime] = token
        token.setPos(pos)
        self.provider.rtoken.addToken(token)
        if isinstance(token, MobMime | NPCMime):
            self._names[token.mime.name] += 1
        self.token_added.emit(token, pos)
    
    def moveToken(self, pos: QPointF, token: BaseToken):
        token.setPos(pos)
        self.token_moved.emit(token.mime, pos)
    
    def removeToken(self, token: BaseToken):
        token = self._tokens.pop(token.mime)
        self.provider.rtoken.removeToken(token)
        self.token_removed.emit(token.mime)
        return token
    
    def moveToMap(self, manager: Manager, pos: QPointF, token: BaseToken):
        self.removeToken(token)
        manager.addToken(pos, token)
        self.token_map_moved.emit(token, pos)
    
    def createToken(self, ttype: str, data: CreateData) -> tuple[BaseToken, Path]:
        if isinstance(data.mime, CacheTokenMime):
            factory = MobMime if ttype == "mob" else NPCMime
            if data.mime.unique:
                data.mime = factory(name=data.mime.name, number="Unique")
            else:
                data.mime = factory(name=data.mime.name, number=self._names.setdefault(data.mime.name, 0))
        match data.mime:
            case PlayerMime():
                return PlayerToken.create(data), data.avatar
            case MobMime():
                return MobToken.create(data), data.avatar
            case NPCMime():
                return NPCToken.create(data), data.avatar
            case SpawnMime():
                return SpawnPlayerToken.create(data), data.avatar
    
    def createTokenFromInput(self, imime: InputMime) -> tuple[BaseToken, Path]:
        data = None
        match imime.category:
            case "spawnplayer":
                data = CreateData(SpawnMime(), 1.0)
            case "mob":
                data = DialogCreateToken.request("Моба")
                if not data:
                    return None, None
            case "npc":
                data = DialogCreateToken.request("НПС")
                if not data:
                    return None, None
        return self.createToken(imime, data)

    def createPlayerToken(self, name, cls, uid, avatar="") -> tuple[BaseToken, Path]:
        data = CreateData(
            PlayerMime(name=name, cls=cls, uid=uid), 1.0,
            "", avatar
        )
        return self.createToken("player", data)
    