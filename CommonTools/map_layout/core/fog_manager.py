import base64
import math
import struct
import zlib

from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject
from PySide6.QtGui import QPainterPath, QColor, QPolygonF, QPainterPathStroker, QBrush, QPixmap
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsScene, QGraphicsPolygonItem, QGraphicsItem


def serialize_path(path: QPainterPath) -> list:
    """Превращает путь в список полигонов для отправки по сети."""
    polygons = path.toFillPolygons()
    encoded_polys = []
    
    for poly in polygons:
        flat_coords = []
        for p in poly:
            flat_coords.append(int(p.x() * 10))
            flat_coords.append(int(p.y() * 10))
        binary_data = struct.pack(f'<{len(flat_coords)}i', *flat_coords)
        compressed = zlib.compress(binary_data)
        b64_str = base64.b64encode(compressed).decode('utf-8')
        encoded_polys.append(b64_str)
    return encoded_polys


def deserialize_path(data: list) -> QPainterPath:
    """Восстанавливает путь из данных сети."""
    path = QPainterPath()
    
    for b64_str in data:
        try:
            compressed = base64.b64decode(b64_str)
            binary_data = zlib.decompress(compressed)
            count = len(binary_data) // 4
            flat_coords = struct.unpack(f'<{count}i', binary_data)
            polygon = QPolygonF()
            for i in range(0, len(flat_coords), 2):
                x = flat_coords[i] / 10.0
                y = flat_coords[i + 1] / 10.0
                polygon.append(QPointF(x, y))
            path.addPolygon(polygon)
        except Exception as e:
            print(f"Error decoding fog chunk: {e}")
            continue
    return path


class VectorFogManager(QObject):
    fog_changed = Signal(bool, list)
    
    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        
        self.fog_path_item: QGraphicsPathItem | None = None
        self.current_path = QPainterPath()
        
        self.temp_items: list[QGraphicsItem] = []
        
        # Настройки
        self.brush_size = 60
        pix = QPixmap(":/textures/fog.png")
        self.brush = QBrush(QColor(0, 0, 0) if pix.isNull() else pix)
        
        self.step_size = 15
        self.vertex_limit = 10000
        
        self.cached_brush_polygon: QPolygonF | None = None
        self.last_brush_size = -1
        
        self.is_active = False
        self.is_revealing = True
        self.last_pos = None
        
        self.master_opacity = 0.45
        self.player_opacity = 1.0
        self.current_opacity = self.master_opacity
        
        self.stroke_path = QPainterPath()
    
    def clear(self):
        self.fog_path_item = None
        self.current_path = QPainterPath()
        self._clear_temp_items()
    
    def _clear_temp_items(self):
        """Удаляет временные элементы со сцены"""
        for item in self.temp_items:
            self.scene.removeItem(item)
        self.temp_items.clear()
    
    def init_fog(self, rect: QRectF):
        if not rect: return
        
        if self.fog_path_item:
            self.scene.removeItem(self.fog_path_item)
        
        self.current_path = QPainterPath()
        self.current_path.addRect(rect)
        
        self.fog_path_item = QGraphicsPathItem(self.current_path)
        self.fog_path_item.setPen(Qt.PenStyle.NoPen)
        self.fog_path_item.setBrush(self.brush)
        self.fog_path_item.setZValue(8000)
        self.fog_path_item.setOpacity(self.current_opacity)
        self.fog_path_item.setAcceptHoverEvents(False)
        self.fog_path_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        self.scene.addItem(self.fog_path_item)
    
    def _get_brush_polygon(self, size):
        if self.cached_brush_polygon and self.last_brush_size == size:
            return self.cached_brush_polygon
        
        segments = 12
        polygon = QPolygonF()
        radius = size / 2
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            polygon.append(QPointF(x, y))
        polygon.append(polygon.at(0))
        
        self.cached_brush_polygon = polygon
        self.last_brush_size = size
        return polygon
    
    def _setup_temp_item(self, item):
        """Настройка шлейфа"""
        item.setPen(Qt.PenStyle.NoPen)
        # Явно ставим ZValue выше тумана
        item.setZValue(8001)
        
        if self.is_revealing:
            # Красный полупрозрачный след (Ластик)
            item.setBrush(QColor(255, 0, 0, 100))
        else:
            # Черный след (Рисование тумана)
            item.setBrush(QColor(0, 0, 0))
            item.setOpacity(self.current_opacity)
    
    def start_stroke(self):
        self.stroke_path = QPainterPath()
        self.stroke_path.setFillRule(Qt.FillRule.WindingFill)
        self.last_pos = None
        
        # Очищаем старый шлейф
        self._clear_temp_items()
    
    def add_stroke_point(self, scene_pos: QPointF):
        if not self.fog_path_item or scene_pos is None:
            return
        
        # 1. Первая точка
        if self.last_pos is None:
            self.last_pos = scene_pos
            poly_shape = self._get_brush_polygon(self.brush_size)
            translated_poly = poly_shape.translated(scene_pos)
            
            self.stroke_path.addPolygon(translated_poly)
            
            # Визуал
            temp_item = QGraphicsPolygonItem(translated_poly)
            self._setup_temp_item(temp_item)
            
            # Добавляем НА СЦЕНУ и В СПИСОК
            self.scene.addItem(temp_item)
            self.temp_items.append(temp_item)
            return
        
        # 2. Дистанция
        dist = (scene_pos - self.last_pos).manhattanLength()
        if dist < self.step_size:
            return
        
        # 3. Линия
        line_path = QPainterPath()
        line_path.moveTo(self.last_pos)
        line_path.lineTo(scene_pos)
        
        stroker = QPainterPathStroker()
        stroker.setWidth(self.brush_size)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        stroker.setMiterLimit(10)
        
        thick_segment = stroker.createStroke(line_path)
        self.stroke_path.addPath(thick_segment)
        
        # Визуал
        temp_item = QGraphicsPathItem(thick_segment)
        self._setup_temp_item(temp_item)
        
        # Добавляем НА СЦЕНУ и В СПИСОК
        self.scene.addItem(temp_item)
        self.temp_items.append(temp_item)
        
        self.last_pos = scene_pos
    
    def finish_stroke(self):
        if not self.fog_path_item:
            return
        
        # Удаляем красный шлейф
        self._clear_temp_items()
        
        self.stroke_path = self.stroke_path.simplified()
        if self.stroke_path.isEmpty():
            return
        
        stroke_data = serialize_path(self.stroke_path)
        
        if self.is_revealing:
            self.current_path = self.current_path.subtracted(self.stroke_path)
        else:
            self.current_path = self.current_path.united(self.stroke_path)
        
        if self.current_path.elementCount() > self.vertex_limit:
            self.current_path = self.current_path.simplified()
        
        self.fog_path_item.setPath(self.current_path)
        
        self.fog_changed.emit(self.is_revealing, stroke_data)
    
    # ... Остальные методы (set_view_mode, handle_mouse_..., apply_diff, full_state) без изменений ...
    # (Не забудь скопировать методы fill_all / reveal_all из предыдущих ответов если нужны)
    
    def set_view_mode(self, is_master: bool):
        self.current_opacity = self.master_opacity if is_master else self.player_opacity
        if self.fog_path_item:
            self.fog_path_item.setOpacity(self.current_opacity)
        # Также обновляем прозрачность текущего шлейфа, если он есть
        for item in self.temp_items:
            if not self.is_revealing:  # Красный ластик не меняет прозрачность
                item.setOpacity(self.current_opacity)
    
    def handle_mouse_press(self, event, map_to_scene_func):
        if not self.is_active: return False
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_stroke()
            pos = map_to_scene_func(event.pos())
            if pos: self.add_stroke_point(pos)
            return True
        return False
    
    def handle_mouse_move(self, event, map_to_scene_func):
        if not self.is_active: return False
        if event.buttons() & Qt.MouseButton.LeftButton:
            pos = map_to_scene_func(event.pos())
            if pos: self.add_stroke_point(pos)
            return True
        return False
    
    def handle_mouse_release(self, event):
        if not self.is_active: return False
        if event.button() == Qt.MouseButton.LeftButton:
            self.finish_stroke()
            return True
        return False
    
    def apply_diff(self, is_revealing: bool, stroke_data: list):
        if not self.fog_path_item: return
        remote_stroke = deserialize_path(stroke_data)
        if is_revealing:
            self.current_path = self.current_path.subtracted(remote_stroke)
        else:
            self.current_path = self.current_path.united(remote_stroke)
        self.fog_path_item.setPath(self.current_path)
    
    def get_full_state(self):
        return serialize_path(self.current_path)
    
    def set_full_state(self, state_data: list):
        if not self.fog_path_item: return
        self.current_path = deserialize_path(state_data)
        self.fog_path_item.setPath(self.current_path)
    
    def fill_all(self):
        """Залить всю карту туманом (Сброс в черноту)"""
        if not self.fog_path_item or not self.scene.sceneRect():
            return
        
        full_rect_path = QPainterPath()
        full_rect_path.addRect(self.scene.sceneRect())
        
        self.current_path = full_rect_path
        self.fog_path_item.setPath(self.current_path)
        
        data = serialize_path(full_rect_path)
        self.fog_changed.emit(False, data)
    
    def reveal_all(self):
        """Убрать весь туман (Открыть карту полностью)"""
        if not self.fog_path_item or not self.scene.sceneRect():
            return
        full_rect_path = QPainterPath()
        full_rect_path.addRect(self.scene.sceneRect())
        
        self.current_path = QPainterPath()
        self.fog_path_item.setPath(self.current_path)
        
        data = serialize_path(full_rect_path)
        self.fog_changed.emit(True, data)
