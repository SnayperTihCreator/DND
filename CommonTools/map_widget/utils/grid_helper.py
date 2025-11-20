from PySide6.QtCore import QPointF


class GridHelper:
    def __init__(self, scene):
        self.scene = scene
    
    def get_grid_size(self):
        """Возвращает размер сетки карты"""
        for item in self.scene.items():
            if hasattr(item, 'grid_size'):
                return item.grid_size
        return 50  # значение по умолчанию
    
    def align_to_grid(self, position: QPointF, grid_size=None):
        """Выравнивает позицию по центру ячейки сетки"""
        if grid_size is None:
            grid_size = self.get_grid_size()
        
        cell_center_x = round(position.x() / grid_size) * grid_size + grid_size / 2
        cell_center_y = round(position.y() / grid_size) * grid_size + grid_size / 2
        return QPointF(cell_center_x, cell_center_y)