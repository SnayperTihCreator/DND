import logging
from PySide6.QtCore import QPoint

from CommonTools.messages import *
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
    
    def _handle_custom_message(self, msg: BaseMessage):
        logger.debug("Handling custom message type: %s", msg.type)
        match msg.type:
            case MapActionType.MAP_CREATE:
                return self._handle_create_map(msg)
            case MapActionType.MAP_DELETE:
                return self._handle_delete_map(msg)
            case MapActionType.MAP_ACTIVE:
                return self._handle_active_map(msg)
            case MapActionType.MAP_GRID_DATA:
                return self._handle_grid_data(msg)
            case MapActionType.PLAYER_FREEZE:
                return self._handle_change_freeze(msg)
            case _:
                logger.warning("No handler found in PlayerController for message type: %s", msg.type)
                return False
    
    def _handle_create_map(self, msg: MapCreateMap):
        logger.info("Handling MAP_CREATE: Adding map '%s' with visibility %s.", msg.name, msg.visible)
        return self.tabMaps.addMap(msg.name, msg.visible)
    
    def _handle_delete_map(self, msg: MapDeleteMap):
        logger.info("Handling MAP_DELETE: Removing map '%s'.", msg.name)
        return self.tabMaps.removeMap(msg.name)
    
    def _handle_active_map(self, msg: MapActiveMap):
        logger.info("Handling MAP_ACTIVE: Activating map '%s'.", msg.name)
        return self.tabMaps.activeMap(msg.name)
    
    def _handle_grid_data(self, msg: MapGridData):
        offset = QPoint(msg.offset[0], msg.offset[1])
        logger.info("Handling MAP_GRID_DATA: Setting grid offset to %s and size to %s.", offset.toTuple(), msg.size)
        self.tabMaps.call_all_method("setOffsetSize", offset, msg.size)
        return True
    
    def _handle_change_freeze(self, msg: MapFreezePlayer):
        logger.info("Handling PLAYER_FREEZE: Setting token freeze to %s.", msg.freeze)
        self.tabMaps.call_all_method("setFreezeToken", msg.freeze)
        return True
