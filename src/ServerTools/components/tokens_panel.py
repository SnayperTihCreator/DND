from PySide6.QtCore import Qt, QMimeData, Signal, QSize
from PySide6.QtGui import QDrag, QIcon, QMouseEvent
from PySide6.QtWidgets import QWidget, QDockWidget, QToolButton, QGridLayout


class DraggableButton(QToolButton):
    def __init__(self, text, icon_path, mime_data, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.mime_data = mime_data
        
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(40, 40))
        self.setFixedSize(90, 85)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self.setIcon(QIcon(icon_path))
        self.setStyleSheet("""
        QToolButton {{
                background-color: {icon_color};
                color: white;
                border-radius: 12px;
                border: none;
                font-weight: bold;
                padding: 5px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.2); /* Эффект объема */
            }}
            QToolButton:hover {{
                border-bottom: 6px solid rgba(0, 0, 0, 0.2);
                margin-top: -2px; /* Приподнимается */
            }}
            QToolButton:pressed {{
                border-bottom: 0px solid transparent;
                margin-top: 4px; /* Вдавливается */
            }}
        """)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.mime_data)
            drag.setMimeData(mime)
            
            pixmap = self.icon().pixmap(20, 20)
            drag.setPixmap(pixmap)
            
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            super().mousePressEvent(event)


class TokensPanel(QDockWidget):
    confirming = Signal()
    
    def __init__(self):
        super().__init__("Панель токенов")
        self.setMinimumWidth(200)
        self.cw = QWidget()
        layout = QGridLayout(self.cw)
        
        self.player_token = DraggableButton("Спавн", ":/icons/token/spawn.svg", "spawn:player")
        layout.addWidget(self.player_token, 0, 0)
        
        self.mob_token = DraggableButton("Моб", ":/icons/token/mob.svg", "mob:request")
        layout.addWidget(self.mob_token, 1, 0)
        
        self.npc_token = DraggableButton("НПС", ":/icons/token/npc.svg", "npc:request")
        layout.addWidget(self.npc_token, 1, 1)
        self.setWidget(self.cw)
