from enum import IntEnum, auto

from PySide6.QtGui import QMouseEvent, QPen, QColor
from PySide6.QtWidgets import QListView, QStyledItemDelegate, QWidget, QStyleOptionButton, QStyle, QApplication, \
    QVBoxLayout, QCheckBox, QDockWidget
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QSize, QRect, QEvent, Signal
from attrs import define, field


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
        self._players: list[PlayerItem] = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._players)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._players):
            return None
        
        match role:
            case Qt.ItemDataRole.DisplayRole:
                return self._players[index.row()].name
            case PlayerItemRole.CLASS_ROLE:
                return self._players[index.row()].cls
            case PlayerItemRole.ACTIVE_ROLE:
                return self._players[index.row()].active
            case PlayerItemRole.UID_ROLE:
                return self._players[index.row()].uid
    
    def setData(self, index, value, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._players):
            return False
        
        match role:
            case PlayerItemRole.ACTIVE_ROLE:
                self._players[index.row()].active = value
                self.dataChanged.emit(index, index, [PlayerItemRole.ACTIVE_ROLE])
                return True
    
    def addPlayer(self, player: PlayerItem):
        self.beginInsertRows(QModelIndex(), len(self._players), len(self._players))
        self._players.append(player)
        self.endInsertRows()
    
    def removeByUidPlayer(self, uid: str):
        for i, player in enumerate(self._players):
            if player.uid == uid:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._players.pop(i)
                self.endRemoveRows()
                return
    
    def getPlayerByUid(self, uid: str):
        for player in self._players:
            if player.uid == uid:
                return player
        return None
    
    def getAllPlayer(self):
        return self._players[:]
    
    def setActivePlayer(self, player, active):
        idx = self._players.index(player)
        self.setData(self.createIndex(idx, 0), active, PlayerItemRole.ACTIVE_ROLE)
    
    def clear(self):
        self.beginResetModel()
        self._players.clear()
        self.endResetModel()


class PlayerPanelDelegate(QStyledItemDelegate):
    active_change = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def sizeHint(self, option, index, /):
        return QSize(200, 50)
    
    def paint(self, painter, option, index, /):
        painter.save()
        self.initStyleOption(option, index)
        
        player_name = index.data(Qt.ItemDataRole.DisplayRole)
        player_cls = index.data(PlayerItemRole.CLASS_ROLE)
        player_active = index.data(PlayerItemRole.ACTIVE_ROLE)
        
        checkbox_option = QStyleOptionButton()
        checkbox_option.rect = option.rect.adjusted(0, 14, -option.rect.width() + 48, -14)
        checkbox_option.state = QStyle.StateFlag.State_Enabled
        checkbox_option.state |= QStyle.StateFlag.State_On if player_active else QStyle.StateFlag.State_Off
        QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, checkbox_option, painter)
        
        text_rect = option.rect.adjusted(50, 0, 0, 0)
        painter.drawText(text_rect, f"Имя: {player_name}", Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        painter.drawText(text_rect, f"Класс: {player_cls}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        painter.restore()
        
        painter.save()
        painter.setBrush("#00000000")
        painter.setPen(QPen(QColor("#fff"), 3))
        painter.drawRoundedRect(option.rect, 10, 10)
        painter.restore()
    
    def editorEvent(self, event, model, option, index):
        checkbox_rect: QRect = option.rect.adjusted(0, 14, -option.rect.width() + 48, -14)
        if isinstance(event, QMouseEvent) and event.type() == QEvent.Type.MouseButtonPress:
            if checkbox_rect.contains(event.pos()) and event.button() == Qt.MouseButton.LeftButton:
                active = index.data(PlayerItemRole.ACTIVE_ROLE)
                model.setData(index, not active, PlayerItemRole.ACTIVE_ROLE)
                self.active_change.emit(index.data(PlayerItemRole.UID_ROLE))
                return True
        return super().editorEvent(event, model, option, index)


class PlayerPanel(QDockWidget):
    active_change = Signal(str, bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель игроков")
        self.cw = QWidget()
        self.setWidget(self.cw)
        self.box = QVBoxLayout(self.cw)
        
        self.checkbox_active = QCheckBox("Все активны")
        self.checkbox_active.checkStateChanged.connect(self._handle_state_checkbox)
        self.listView = QListView()
        self.box.addWidget(self.checkbox_active)
        self.box.addWidget(self.listView)
        self.modelList = PlayerPanelModel()
        self.delegateList = PlayerPanelDelegate(self.listView)
        self.delegateList.active_change.connect(self._handle_change_state)
        
        self.listView.setModel(self.modelList)
        self.listView.setItemDelegate(self.delegateList)
    
    def _handle_state_checkbox(self, state):
        match state:
            case Qt.CheckState.Checked:
                for player in self.modelList.getAllPlayer():
                    self.modelList.setActivePlayer(player, True)
            case Qt.CheckState.Unchecked:
                for player in self.modelList.getAllPlayer():
                    self.modelList.setActivePlayer(player, False)
    
    def _handle_change_state(self, uid):
        actives = [player.active for player in self.modelList.getAllPlayer()]
        act1, act2 = all(actives), any(actives)
        if act1 and act2:
            self.checkbox_active.setCheckState(Qt.CheckState.Checked)
        elif not act1 and act2:
            self.checkbox_active.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            self.checkbox_active.setCheckState(Qt.CheckState.Unchecked)
        if uid:
            self.active_change.emit(uid, self.modelList.getPlayerByUid(uid).active)
    
    def addPlayer(self, uid, name, cls):
        self.modelList.addPlayer(PlayerItem(uid, name, cls))
        self._handle_change_state(uid)
    
    def removePlayer(self, uid):
        self.modelList.removeByUidPlayer(uid)
        self._handle_change_state("")
    
    def clear(self):
        self.modelList.clear()
