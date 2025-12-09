from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsScene, QGraphicsPolygonItem, QGraphicsItemGroup
from PySide6.QtGui import QPainterPath, QColor, QBrush, QPen, QPolygonF
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject
import math


def serialize_path(path: QPainterPath):
    """Превращает путь в список полигонов: [[[x,y], [x,y]], [...]]"""
    polygons = path.toFillPolygons()
    result = []
    for poly in polygons:
        points = []
        for p in poly:
            points.append((round(p.x(), 1), round(p.y(), 1)))  # Округляем для экономии байт
        result.append(points)
    return result


def deserialize_path(data: list) -> QPainterPath:
    """Восстанавливает путь из списка полигонов"""
    path = QPainterPath()
    for poly_points in data:
        polygon = QPolygonF()
        for x, y in poly_points:
            polygon.append(QPointF(x, y))
        path.addPolygon(polygon)
    return path


class VectorFogManager(QObject):
    fog_changed = Signal(bool, list)
    
    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        
        self.fog_path_item: QGraphicsPathItem | None = None
        self.current_path = QPainterPath()
        
        self.temp_group = QGraphicsItemGroup()
        self.scene.addItem(self.temp_group)
        self.temp_group.setZValue(8001)
        
        self.brush_size = 60
        self.step_size = 15
        self.vertex_limit = 10000
        
        self.cached_brush_polygon: QPolygonF | None = None
        self.last_brush_size = -1
        
        self.is_active = False
        self.is_revealing = True
        self.last_pos = None
        
        self.master_opacity = 0.5
        self.player_opacity = 1.0
        self.current_opacity = self.master_opacity
        
        self.stroke_path = QPainterPath()
        
    def clear(self):
        self.fog_path_item = None
    
    def _get_brush_polygon(self, size):
        """Создает 12-угольник вместо идеального круга для скорости"""
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
    
    def init_fog(self, rect: QRectF):
        if self.fog_path_item:
            self.scene.removeItem(self.fog_path_item)
        
        self.current_path = QPainterPath()
        self.current_path.addRect(rect)
        
        self.fog_path_item = QGraphicsPathItem(self.current_path)
        self.fog_path_item.setPen(Qt.PenStyle.NoPen)
        self.fog_path_item.setBrush(QColor(0, 0, 0))
        self.fog_path_item.setZValue(8000)
        self.fog_path_item.setOpacity(self.current_opacity)
        self.fog_path_item.setAcceptHoverEvents(False)
        self.fog_path_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        self.scene.addItem(self.fog_path_item)
    
    def start_stroke(self):
        self.stroke_path = QPainterPath()
        self.stroke_path.setFillRule(Qt.FillRule.WindingFill)
        self.last_pos = None  # Сброс последней позиции
        
        # Очистка визуала
        for child in self.temp_group.childItems():
            self.scene.removeItem(child)
    
    def add_stroke_point(self, scene_pos: QPointF):
        if not self.fog_path_item: return
        
        # ОПТИМИЗАЦИЯ 1: Проверка дистанции (Step)
        if self.last_pos:
            dist = (scene_pos - self.last_pos).manhattanLength()
            if dist < self.step_size:
                return  # Слишком маленькое движение, пропускаем
        
        self.last_pos = scene_pos
        
        
        # ОПТИМИЗАЦИЯ 2: Использование полигона вместо addEllipse
        poly_shape = self._get_brush_polygon(self.brush_size)
        # Сдвигаем полигон в точку мыши
        translated_poly = poly_shape.translated(scene_pos)
        
        # Добавляем в путь штриха
        self.stroke_path.addPolygon(translated_poly)
        
        # ВИЗУАЛ: Рисуем временный многоугольник
        temp_item = QGraphicsPolygonItem(translated_poly)
        temp_item.setPen(Qt.PenStyle.NoPen)
        
        if self.is_revealing:
            temp_item.setBrush(QColor(255, 0, 0, 100))  # Красный полупрозрачный ластик
        else:
            temp_item.setBrush(QColor(0, 0, 0))
            temp_item.setOpacity(self.current_opacity)
        
        self.temp_group.addToGroup(temp_item)
    
    def finish_stroke(self):
        """Завершение рисования Мастером"""
        if not self.fog_path_item:
            return
        
        # Удаляем временные элементы
        for child in self.temp_group.childItems():
            self.scene.removeItem(child)
        
        # 1. Упрощаем штрих
        self.stroke_path = self.stroke_path.simplified()
        
        # 2. СЕРИАЛИЗАЦИЯ: Превращаем штрих в данные ПЕРЕД слиянием
        # Если штрих пустой, ничего не делаем
        if self.stroke_path.isEmpty():
            return
        
        stroke_data = serialize_path(self.stroke_path)
        
        # 3. Применяем локально
        if self.is_revealing:
            self.current_path = self.current_path.subtracted(self.stroke_path)
        else:
            self.current_path = self.current_path.united(self.stroke_path)
        
        # Авто-упрощение (если нужно)
        if self.current_path.elementCount() > self.vertex_limit:
            self.current_path = self.current_path.simplified()
        
        self.fog_path_item.setPath(self.current_path)
        
        # 4. ОТПРАВКА В СЕТЬ
        # Отправляем: True (если стираем), data (точки штриха)
        self.fog_changed.emit(self.is_revealing, stroke_data)
    
    # --- Standard Handlers ---
    def set_view_mode(self, is_master: bool):
        self.current_opacity = self.master_opacity if is_master else self.player_opacity
        if self.fog_path_item:
            self.fog_path_item.setOpacity(self.current_opacity)
        self.temp_group.setOpacity(self.current_opacity)
    
    def handle_mouse_press(self, event, map_to_scene_func):
        if not self.is_active: return False
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_stroke()
            self.add_stroke_point(map_to_scene_func(event.pos()))
            return True
        return False
    
    def handle_mouse_move(self, event, map_to_scene_func):
        if not self.is_active: return False
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.add_stroke_point(map_to_scene_func(event.pos()))
            return True
        return False
    
    def handle_mouse_release(self, event):
        if not self.is_active: return False
        if event.button() == Qt.MouseButton.LeftButton:
            self.finish_stroke()
            return True
        return False
    
    def apply_diff(self, is_revealing: bool, stroke_data: list):
        """Применяет пришедший из сети штрих"""
        if not self.fog_path_item: return
        
        # 1. Восстанавливаем QPainterPath из JSON-данных
        remote_stroke = deserialize_path(stroke_data)
        
        # 2. Применяем математику
        if is_revealing:
            self.current_path = self.current_path.subtracted(remote_stroke)
        else:
            self.current_path = self.current_path.united(remote_stroke)
        
        # 3. Обновляем визуал
        self.fog_path_item.setPath(self.current_path)
    
    def get_full_state(self):
        """Возвращает ПОЛНЫЙ слепок тумана (для новых игроков)"""
        # Внимание: это может быть большим объектом!
        return serialize_path(self.current_path)
    
    def set_full_state(self, state_data: list):
        """Загружает полный слепок тумана"""
        if not self.fog_path_item: return
        
        new_path = deserialize_path(state_data)
        self.current_path = new_path
        self.fog_path_item.setPath(self.current_path)
