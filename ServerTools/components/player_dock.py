from PySide6.QtWidgets import QDockWidget

from .player_panel import PlayerSelectionWidget, PlayerItem


class PlayerPanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Панель игроков", parent)
        self.selection_widget = PlayerSelectionWidget()
        self.setWidget(self.selection_widget)
        
        # Пробрасываем сигнал наружу, если кто-то на него подписан
        self.active_change = self.selection_widget.active_change
        
    def addPlayer(self, uid, name, cls):
        self.selection_widget.addPlayer(uid, name, cls)
    
    def removePlayer(self, uid):
        self.selection_widget.removePlayer(uid)
        
    def getAllPlayers(self):
        return self.selection_widget.getAllPlayers()
    
