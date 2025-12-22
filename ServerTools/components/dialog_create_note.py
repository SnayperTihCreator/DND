from PySide6.QtWidgets import QDialog, QSplitter, QVBoxLayout, QDialogButtonBox

from CommonTools.notes.editor import NoteEditor
from .player_panel import PlayerItem
from .player_panel import PlayerSelectionWidget


class DialogCreateNote(QDialog):
    def __init__(self, players: list[PlayerItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Note")
        self.resize(800, 600)
        
        self.box = QVBoxLayout(self)
        self.splitter = QSplitter(self)
        self.box.addWidget(self.splitter)
        
        self.editor = NoteEditor()
        self.players = PlayerSelectionWidget()
        [self.players.addPlayer(player.uid, player.name, player.cls) for player in players]
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.players)
        
    @classmethod
    def request(cls, parent, players: list[PlayerItem]):
        dialog = DialogCreateNote(players, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return True
        return False
        
        