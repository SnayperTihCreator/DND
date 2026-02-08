from enum import IntEnum, auto
from typing import Optional, Iterator

from attrs import define, field
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionButton, QApplication, QWidget, QVBoxLayout, \
    QCheckBox, QListView
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, Signal, QSize, QRect, QEvent
from PySide6.QtGui import QPainter, QColor, QPen


class PlayerItemRole(IntEnum):
    CLASS_ROLE = Qt.ItemDataRole.UserRole
    ACTIVE_ROLE = auto()
    UID_ROLE = auto()


@define
class PlayerItem:
    uid: str
    name: str
    cls: str
    active: bool = field(default=False)


class PlayerPanelModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        # Список хранит порядок для View (индексы 0, 1, 2...)
        self._players: list[PlayerItem] = []
        # Словарь хранит ссылки на те же объекты для мгновенного доступа по UID
        self._lookup: dict[str, PlayerItem] = {}
    
    def roleNames(self):
        """Важно для поддержки QML и именованных ролей"""
        roles = super().roleNames()
        roles[PlayerItemRole.CLASS_ROLE] = b"playerClass"
        roles[PlayerItemRole.ACTIVE_ROLE] = b"isActive"
        roles[PlayerItemRole.UID_ROLE] = b"uid"
        return roles
    
    # --- Чтение (Стандартные методы Qt) ---
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._players)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._players)):
            return None
        
        player = self._players[index.row()]
        
        match role:
            case Qt.ItemDataRole.DisplayRole:
                return player.name
            case PlayerItemRole.CLASS_ROLE:
                return player.cls
            case PlayerItemRole.ACTIVE_ROLE:
                return player.active
            case PlayerItemRole.UID_ROLE:
                return player.uid
        return None
    
    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or not (0 <= index.row() < len(self._players)):
            return False
        
        player = self._players[index.row()]
        
        if role == PlayerItemRole.ACTIVE_ROLE:
            if player.active != value:
                player.active = value
                self.dataChanged.emit(index, index, [role])
                return True
        return False
    
    # --- Быстрый доступ и Итерация ---
    
    def getPlayerByUid(self, uid: str) -> Optional[PlayerItem]:
        """Мгновенный поиск O(1)"""
        return self._lookup.get(uid)
    
    def __iter__(self) -> Iterator[PlayerItem]:
        """Позволяет использовать модель в цикле: for player in model: ..."""
        return iter(self._players)
    
    # --- Модификация данных ---
    
    def addPlayer(self, player: PlayerItem):
        if player.uid in self._lookup:
            return
        
        row = len(self._players)
        self.beginInsertRows(QModelIndex(), row, row)
        self._players.append(player)
        self._lookup[player.uid] = player
        self.endInsertRows()
    
    def removeByUidPlayer(self, uid: str):
        if uid not in self._lookup:
            return
        
        # Находим индекс объекта через список
        player = self._lookup[uid]
        row = self._players.index(player)
        
        self.beginRemoveRows(QModelIndex(), row, row)
        self._players.pop(row)
        del self._lookup[uid]
        self.endRemoveRows()
    
    def setActivePlayerByUid(self, uid: str, active: bool):
        """Обновление через UID: безопасно и быстро"""
        player = self._lookup.get(uid)
        if player:
            row = self._players.index(player)
            self.setData(self.index(row, 0), active, PlayerItemRole.ACTIVE_ROLE)
    
    def clear(self):
        self.beginResetModel()
        self._players.clear()
        self._lookup.clear()
        self.endResetModel()


class PlayerPanelDelegate(QStyledItemDelegate):
    active_change = Signal(str)
    
    def sizeHint(self, option, index, /):
        return QSize(200, 60)  # Увеличил высоту для лучшего разделения строк
    
    def paint(self, painter, option, index, /):
        painter.save()
        self.initStyleOption(option, index)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 2. Отрисовка чекбокса
        player_active = index.data(PlayerItemRole.ACTIVE_ROLE)
        
        checkbox_option = QStyleOptionButton()
        # Центрируем чекбокс вертикально
        cb_size = QApplication.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        cb_margin = (option.rect.height() - cb_size) // 2
        checkbox_option.rect = QRect(option.rect.left() + 10, option.rect.top() + cb_margin, cb_size, cb_size)
        
        checkbox_option.state = QStyle.StateFlag.State_Enabled
        checkbox_option.state |= QStyle.StateFlag.State_On if player_active else QStyle.StateFlag.State_Off
        QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, checkbox_option, painter)
        
        # 3. Отрисовка текста (разделяем на 2 зоны)
        text_left_margin = 45
        # Верхняя половина для имени
        name_rect = option.rect.adjusted(text_left_margin, 5, -5, -option.rect.height() // 2)
        # Нижняя половина для класса
        class_rect = option.rect.adjusted(text_left_margin, option.rect.height() // 2, -5, -5)
        
        player_name = index.data(Qt.ItemDataRole.DisplayRole)
        player_cls = index.data(PlayerItemRole.CLASS_ROLE)
        
        painter.setPen(option.palette.text().color())  # Используем цвет темы
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, f"Имя: {player_name}")
        
        painter.setPen(QColor("#888"))  # Класс сделаем чуть тусклее
        painter.drawText(class_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Класс: {player_cls}")
        
        # 4. Отрисовка рамки
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#555"), 1))  # Тонкая серая рамка
        painter.drawRoundedRect(option.rect.adjusted(1, 1, -1, -1), 10, 10)
        
        painter.restore()
    
    def editorEvent(self, event, model, option, index):
        # Логика определения клика по чекбоксу должна совпадать с отрисовкой в paint
        cb_size = QApplication.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        cb_margin = (option.rect.height() - cb_size) // 2
        checkbox_rect = QRect(option.rect.left() + 10, option.rect.top() + cb_margin, cb_size, cb_size)
        
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if checkbox_rect.contains(event.pos()):
                active = index.data(PlayerItemRole.ACTIVE_ROLE)
                model.setData(index, not active, PlayerItemRole.ACTIVE_ROLE)
                uid = index.data(PlayerItemRole.UID_ROLE)
                self.active_change.emit(uid)
                return True
        return super().editorEvent(event, model, option, index)


# Базовый виджет, который можно использовать ВЕЗДЕ
class PlayerSelectionWidget(QWidget):
    active_change = Signal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Чтобы не было двойных отступов
        
        self.checkbox_active = QCheckBox("Все активны")
        self.checkbox_active.clicked.connect(self._handle_master_click)
        
        self.listView = QListView()
        self.layout.addWidget(self.checkbox_active)
        self.layout.addWidget(self.listView)
        
        self.modelList = PlayerPanelModel()
        self.delegateList = PlayerPanelDelegate(self.listView)
        self.delegateList.active_change.connect(self._handle_single_change)
        
        self.listView.setModel(self.modelList)
        self.listView.setItemDelegate(self.delegateList)
    
    def _handle_master_click(self):
        new_state = self.checkbox_active.isChecked()
        for player in self.modelList:
            if player.active != new_state:
                self.modelList.setActivePlayerByUid(player.uid, new_state)
    
    def _handle_single_change(self, uid: str):
        """Когда нажат чекбокс конкретного игрока в списке"""
        player = self.modelList.getPlayerByUid(uid)
        if not player:
            return
        
        self.active_change.emit(uid, player.active)
        self._update_master_checkbox_ui()
    
    def _update_master_checkbox_ui(self):
        """Синхронизация состояния главного чекбокса с моделью"""
        if self.modelList.rowCount() == 0:
            self.checkbox_active.setCheckState(Qt.CheckState.Unchecked)
            return
        
        all_active = all(p.active for p in self.modelList)
        any_active = any(p.active for p in self.modelList)
        
        self.checkbox_active.blockSignals(True)
        if all_active:
            self.checkbox_active.setCheckState(Qt.CheckState.Checked)
        elif any_active:
            self.checkbox_active.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            self.checkbox_active.setCheckState(Qt.CheckState.Unchecked)
        self.checkbox_active.blockSignals(False)
    
    def addPlayer(self, uid, name, cls):
        self.modelList.addPlayer(PlayerItem(uid, name, cls))
        self._update_master_checkbox_ui()
    
    def removePlayer(self, uid):
        self.modelList.removeByUidPlayer(uid)
        self._update_master_checkbox_ui()
        
    def getAllPlayers(self):
        return list(self.modelList)
    
    def getSelectedPlayers(self):
        for player in self.modelList:
            if not player.active: continue
            yield player.uid
    
    def clear(self):
        self.modelList.clear()
        self._update_master_checkbox_ui()
