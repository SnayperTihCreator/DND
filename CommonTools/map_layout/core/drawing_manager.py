from PySide6.QtGui import QMouseEvent, QColor


class DrawingManager:
    def __init__(self, scene):
        self.scene = scene
        self.drawing = False
        self.last_point = None
        self.interaction_mode = "move"
        
        # Настройки рисования
        self.drawing_color = QColor(255, 0, 0)
        self.drawing_width = 3
        self.current_zoom = 1.0
    
    def set_interaction_mode(self, mode):
        """Устанавливает режим взаимодействия"""
        self.interaction_mode = mode
    
    def set_drawing_color(self, color):
        self.drawing_color = color
    
    def set_drawing_width(self, width):
        self.drawing_width = width
    
    def set_zoom_level(self, zoom):
        self.current_zoom = zoom
    
    def handle_mouse_press(self, event: QMouseEvent):
        """Обработка нажатия мыши"""
        if (event.button() == event.buttons().LeftButton and
                self.interaction_mode == "draw"):
            self.drawing = True
            self.last_point = event.pos()  # Будет преобразовано в сцену позже
            return True
        return False
    
    def handle_mouse_move(self, event: QMouseEvent, map_to_scene_func):
        """Обработка движения мыши"""
        if self.drawing and self.last_point:
            current_scene_point = map_to_scene_func(event.pos())
            last_scene_point = map_to_scene_func(self.last_point)
            self.last_point = event.pos()
            return True
        return False
    
    def handle_mouse_release(self, event: QMouseEvent):
        """Обработка отпускания мыши"""
        if event.button() == event.buttons().LeftButton and self.drawing:
            self.drawing = False
            self.last_point = None
            return True
        return False