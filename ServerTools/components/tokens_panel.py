from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDockWidget


class TokensPanel(QDockWidget):
    confirming = Signal()
    
    def __init__(self):
        super().__init__("Панель токенов")
        self.setMinimumWidth(200)
        self.cw = QWidget()
        self.setup_ui()
        self.setWidget(self.cw)
    
    def setup_ui(self):
        layout = QVBoxLayout(self.cw)
        
        # Игроки
        self.player_token = QLabel("Спавн")
        self.player_token.setAlignment(Qt.AlignCenter)
        self.player_token.setStyleSheet("background: blue; color: white; padding: 10px; border-radius: 20px;")
        self.player_token.setMaximumWidth(100)
        self.player_token.mousePressEvent = self.start_player_drag
        layout.addWidget(self.player_token)
        
        # Мобы
        self.mob_label = QLabel("Моб")
        self.mob_label.setAlignment(Qt.AlignCenter)
        self.mob_label.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 17px;")
        self.mob_label.setMaximumWidth(100)
        self.mob_label.mousePressEvent = self.start_mob_drag
        layout.addWidget(self.mob_label)
        
        # NPC
        self.npc_label = QLabel("NPC")
        self.npc_label.setAlignment(Qt.AlignCenter)
        self.npc_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 17px;")
        self.npc_label.setMaximumWidth(100)
        self.npc_label.mousePressEvent = self.start_npc_drag
        layout.addWidget(self.npc_label)
        
        layout.addStretch()
    
    def start_drag(self, mime_text):
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(mime_text)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)
    
    def start_player_drag(self, event):
        self.start_drag("spawn:player")
    
    def start_mob_drag(self, event):
        self.start_drag(f"mob:request")
    
    def start_npc_drag(self, event):
        self.start_drag(f"npc:request")
