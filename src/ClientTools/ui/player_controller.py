import logging
from pathlib import Path

from PySide6.QtCore import QPoint

from CommonTools.messages import *
from CommonTools.mime import AssetsMime
from CommonTools.ui.base_controller import BaseController
from ClientTools.core import AsyncClientBridge

logger = logging.getLogger(__name__)


class PlayerController(BaseController):
    
    def __init__(self, socket: AsyncClientBridge):
        super().__init__(socket, socket.me)
        logger.info("Initializing PlayerController...")
        
        layers_to_disable = ["players", "mobs", "npcs", "spawn_point"]
        self.tabMaps.set_token_movement(layers_to_disable, False)
        logger.debug("Disabling token movement for layers: %s", layers_to_disable)
        
        self.tabMaps.call_all_method("setMasterView", False)
        logger.debug("Setting master view to: False")
        
        self.tabMaps.call_all_method("setOffsetSize", QPoint(0, 0), 50)
        logger.debug("Setting initial grid offset and size.")
        
        self.tabMaps.call_all_method("setFreezeToken", True)
        logger.debug("Setting initial token freeze to: True")
        
        self.set_visible_token(["spawn_point"], False)
        logger.debug("Hiding 'spawn_point' token layer.")
        
        self.active = False
        self.buffer.enable(True)
        logger.info("PlayerController initialization complete.")
    
    async def _handle_custom_message(self, msg: BaseMessage):
        pass
    
    @BaseController.router.handler(MapActionType.MAP_CREATE)
    def _handle_create_map(self, _, msg: MapCreateMap):
        logger.info("Handling MAP_CREATE: Adding map '%s' with visibility %s.", msg.name, msg.visible)
        return self.tabMaps.addMap(msg.name, msg.visible)
    
    @BaseController.router.handler(MapActionType.MAP_DELETE)
    def _handle_delete_map(self, _, msg: MapDeleteMap):
        logger.info("Handling MAP_DELETE: Removing map '%s'.", msg.name)
        return self.tabMaps.removeMap(msg.name)
    
    @BaseController.router.handler(MapActionType.MAP_ACTIVE)
    def _handle_active_map(self, _, msg: MapActiveMap):
        logger.info("Handling MAP_ACTIVE: Activating map '%s'.", msg.name)
        return self.tabMaps.activeMap(msg.name)
    
    @BaseController.router.handler(MapActionType.MAP_GRID_DATA)
    def _handle_grid_data(self, _, msg: MapGridData):
        offset = QPoint(msg.offset[0], msg.offset[1])
        logger.info("Handling MAP_GRID_DATA: Setting grid offset to %s and size to %s.", offset.toTuple(), msg.size)
        self.tabMaps.call_all_method("setOffsetSize", offset, msg.size)
        return True
    
    @BaseController.router.handler(MapActionType.PLAYER_FREEZE)
    def _handle_change_freeze(self, _, msg: MapFreezePlayer):
        logger.info("Handling PLAYER_FREEZE: Setting token freeze to %s.", msg.freeze)
        self.tabMaps.call_all_method("setFreezeToken", msg.freeze)
        return True
    
    @BaseController.router.handler(MapActionType.LOAD_BACKGROUND)
    def _handle_load_background(self, _, msg: MapLoadBackground):
        self.socket.manager.add_task(msg.filename, self._on_load_background, args=(msg.mime,))
        return True
    
    @BaseController.router.handler(ClientActionType.ADD_PLAYER)
    def _handle_add_player(self, _, msg: ClientAddPlayer):
        self.add_token(msg.map_name, msg.mime, msg.pos)
        logger.info("Adding player token '%s' to map '%s'", msg.name, msg.map_name)
    
    def _on_load_background(self, filename: Path, mime: AssetsMime):
        self.tabMaps.load_map(mime.filename, filename)
        self.clear_buffer(mime.filename)
