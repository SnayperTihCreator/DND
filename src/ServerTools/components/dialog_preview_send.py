from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QDialog, QSplitter, QDialogButtonBox

from CommonTools.notes import NotePreviewWidget, Note
from .player_panel import PlayerSelectionWidget, PlayerItem


class DialogPreviewSend(QDialog):
    def __init__(self, note: Note, players: list[PlayerItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Предпросмотр и отправка")
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.preview = NotePreviewWidget()
        self.preview.set_note(note)
        
        self.players_widget = PlayerSelectionWidget()
        [self.players_widget.addPlayer(p.uid, p.name, p.cls) for p in players]
        
        splitter.addWidget(self.players_widget)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 3)
        layout.addWidget(splitter)
        
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btns.button(QDialogButtonBox.StandardButton.Ok).setText("Отправить")
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        
        layout.addWidget(self.btns)
    
    @classmethod
    def request(cls, parent, note: Note, players: list[PlayerItem]):
        dialog = cls(note, players, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted, dialog.players_widget.getSelectedPlayers()
