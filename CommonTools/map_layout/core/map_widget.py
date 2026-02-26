from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPointF, Signal, QPoint
from PySide6.QtGui import QMouseEvent, QKeyEvent, QWheelEvent, QPainter, QCursor
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem, QMenu, QApplication, QMessageBox

from .token_manager import TokenManager
from .drawing_manager import DrawingManager
from .view_controller import ViewController
from .fog_manager import VectorFogManager
from .graphics_scene import GraphicsScene
from CommonTools.map_layout.tokens_dnd import *
from CommonTools.core import ClientData
from CommonTools.utils import getImageMIME


class MapWidget(QGraphicsView):
    token_added = Signal(object)
    token_removed = Signal(object)
    token_moved = Signal(object, tuple)
    
    token_moved_map = Signal(object, str)
    fog_changed = Signal(bool, list)
    request_image = Signal(str, str)
    
    def __init__(self, name, client: ClientData):
        super().__init__()
        self.name = name
        self.setMinimumSize(500, 500)
        
        self.g_scene = GraphicsScene()
        self.g_scene.contextMenuRequested.connect(self._handle_context_menu)
        self.g_scene.item_added.connect(self._handle_token_add)
        self.g_scene.item_removed.connect(self._handle_token_remove)
        self.g_scene.item_moved.connect(self._handle_token_move)
        self.g_scene.item_moved2.connect(self._handle_token_move_map)
        self.setScene(self.g_scene)
        
        # Инициализация менеджеров
        self.view_controller = ViewController(self)
        self.token_manager = TokenManager(self.g_scene)
        self.drawing_manager = DrawingManager(self.g_scene)
        self.fog_manager = VectorFogManager(self.g_scene)
        self.fog_manager.fog_changed.connect(self.fog_changed)
        
        self.client: ClientData = client
        self.token_spawn: Optional[SpawnPlayerToken] = None
        self.file_map: Optional[Path] = None
        self.freeze = False
        
        self._setup_view()
        
        self.movement_settings = {
            'players': True,  # Игроки не перемещаются в режиме игрока
            'mobs': True,  # Мобы не перемещаются в режиме игрока
            'npcs': True,  # НПС не перемещаются в режиме игрока
            'spawn_point': True,  # Точка появления всегда перемещается только мастером
        }
    
    def clear(self):
        self.view_controller.clear()
        for item in self.items():
            if isinstance(item, BaseToken):
                self.token_manager.remove_token(item.mime())
            elif isinstance(item, MapWithGridItem):
                continue
            else:
                self.g_scene.removeItem(item)
        del self.token_spawn
        self.token_spawn = None
        self.file_map = None
        self.fog_manager.clear()
    
    def _handle_context_menu(self, pos):
        if not self.freeze:
            return
        menu = QMenu()
        
        action_move = menu.addAction("Переместится")
        
        action = menu.exec(QCursor.pos())
        if action == action_move:
            QApplication.postEvent(QApplication.activeWindow(), MovedEvent(pos))
    
    def setFreezeToken(self, value):
        self.freeze = value
    
    def _handle_token_add(self, item):
        if isinstance(item, BaseToken):
            if item.ttype == "spawn":
                self.token_spawn = item
            self.token_added.emit(item)
    
    def _handle_token_remove(self, item):
        if isinstance(item, BaseToken):
            if item.ttype == "spawn":
                self.token_spawn = None
            self.token_removed.emit(item)
    
    def _handle_token_move_map(self, item, nameMap):
        if isinstance(item, BaseToken):
            self.token_moved_map.emit(item, nameMap)
    
    def _handle_token_move(self, item):
        if isinstance(item, BaseToken):
            self.token_moved.emit(item, item.pos().toTuple())
    
    def set_token_movement(self, token_types: list[str], enabled: bool):
        """Включает/выключает возможность перемещения для типов токенов"""
        for token_type in token_types:
            if token_type in self.movement_settings:
                self.movement_settings[token_type] = enabled
        
        # Применяем настройки ко всем существующим токенам
        self._apply_movement_settings_to_all_tokens()
    
    def _apply_movement_settings_to_all_tokens(self):
        """Применяет настройки перемещения ко всем токенам на сцене"""
        for item in self.g_scene.items():
            if hasattr(item, 'ttype'):
                self._apply_movement_setting_to_token(item)
    
    def _apply_movement_setting_to_token(self, token):
        """Применяет настройки перемещения к конкретному токену"""
        if token is None:
            return
        match getattr(token, 'ttype', None):
            case "player":
                movable = self.movement_settings['players']
            case "mob":
                movable = self.movement_settings['mobs']
            case 'npc':
                movable = self.movement_settings['npcs']
            case 'spawn':
                movable = self.movement_settings['spawn_point']
            case _:
                movable = False  # Остальные токены не перемещаются по умолчанию
        
        token.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)
        token.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, movable)
    
    def _setup_view(self):
        """Настройка отображения"""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    def setTokenMimePos(self, mime: str, pos: tuple[float, float]):
        for item in self.items():
            if isinstance(item, BaseToken) and item.mime() == mime:
                item.setPos(pos[0], pos[1])
    
    # Делегирование методов ViewController
    def setVisibleGrid(self, visible: bool):
        self.view_controller.setVisibleGrid(visible)
    
    def setColorGrid(self, color: str):
        self.view_controller.setColorGrid(color)
    
    def setOffsetSize(self, offset: QPoint, size: int):
        self.view_controller.setOffsetSize(offset, size)
        for item in self.items():
            if isinstance(item, BaseToken):
                item.setPPSize(size)
    
    def load_map(self, file_path):
        self.file_map = file_path
        result = self.view_controller.load_map(file_path)
        rect = self.scene().sceneRect()
        self.fog_manager.init_fog(rect)
        return result
    
    def fit_to_view(self):
        self.view_controller.fit_to_view()
    
    def zoom_in(self):
        self.view_controller.zoom_in()
    
    def zoom_out(self):
        self.view_controller.zoom_out()
    
    def reset_zoom(self):
        self.view_controller.reset_zoom()
    
    # Делегирование методов TokenManager
    def remove_token(self, mime_data: str):
        return self.token_manager.remove_token(mime_data)
    
    def create_token(self, mime_data: str, position: QPointF, scale=1.0):
        token = self.token_manager.create_token(mime_data, position, scale)
        if token is not None:
            token.show()
            self.scene().addItem(token)
            self._apply_movement_setting_to_token(token)
        return token
    
    def create_player(self, name, cls, uid):
        for path in Path(".cache").glob(f"token_{uid}"):
            file = path.as_posix()
            break
        else:
            file = None
        token = self.token_manager.create_token(f"player:{name}:{cls}:{uid}", self.token_spawn.pos())
        if token:
            self.scene().addItem(token)
            self._apply_movement_setting_to_token(token)
            
        if token and file:
            token.setPixmap(file)
        return token
    
    def set_drawing_color(self, color):
        self.drawing_manager.set_drawing_color(color)
    
    def set_drawing_width(self, width):
        self.drawing_manager.set_drawing_width(width)
    
    # Обработчики событий
    def wheelEvent(self, event: QWheelEvent):
        self.view_controller.wheelEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        self.view_controller.keyPressEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        if self.fog_manager.handle_mouse_press(event, self.mapToScene):
            return
        if self.drawing_manager.handle_mouse_press(event):
            return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.fog_manager.handle_mouse_move(event, self.mapToScene):
            return
        if self.drawing_manager.handle_mouse_move(event, self.mapToScene):
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.fog_manager.handle_mouse_release(event):
            return
        
        if self.drawing_manager.handle_mouse_release(event):
            return
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.view_controller.zoom_level == 1.0:
                self.fit_to_view()
            else:
                self.reset_zoom()
        super().mouseDoubleClickEvent(event)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        pos = self.mapToScene(event.pos())
        if not self.file_map:
            QMessageBox.critical(self, "ОШИБКА!!", "ТЫ ЗАЕБАЛ ЗАГРУЗИ ФОН КАРТЫ БЛЯТЬ!")
            event.proposedAction()
            return
        data = event.mimeData().text()
        token = self.create_token(data, pos)
        if token:
            self.request_image.emit(getImageMIME(token.mime()), token.mime())
        event.acceptProposedAction()
    
    @property
    def zoom_level(self):
        return self.view_controller.zoom_level
    
    def setFogMode(self, active: bool, reveal: bool = True):
        """
        Включает режим редактирования тумана.
        active: True = режим включен (двигать карту нельзя, рисуем туман)
        reveal: True = Ластик (открываем карту), False = Кисть (закрываем)
        """
        self.fog_manager.is_active = active
        self.fog_manager.is_revealing = reveal
        
        if active:
            self.drawing_manager.active = False
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
    def isActiveFogMode(self):
        return self.fog_manager.is_active
    
    def isRevealFogMode(self):
        return self.fog_manager.is_revealing
    
    def setFogBrushSize(self, size: int):
        """Размер кисти (диаметр)"""
        self.fog_manager.brush_size = size
    
    def setMasterView(self, is_master: bool):
        """
        True: Туман полупрозрачный (50%)
        False: Туман черный (100%)
        """
        self.fog_manager.set_view_mode(is_master)
        
    def setFogChange(self, is_revealing: bool, stroke_data: list):
        self.fog_manager.apply_diff(is_revealing, stroke_data)
    
    def getFullFog(self):
        return self.fog_manager.get_full_state()
    
    def setFullFog(self, state_data: list):
        self.fog_manager.set_full_state(state_data)
    
    def resetFog(self):
        self.fog_manager.fill_all()
    
    def clearFog(self):
        self.fog_manager.reveal_all()