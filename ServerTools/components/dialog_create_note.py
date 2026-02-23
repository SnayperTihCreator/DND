from typing import Optional

from PySide6.QtWidgets import QDialog, QSplitter, QVBoxLayout, QDialogButtonBox, QSizePolicy
from PySide6.QtCore import Qt

from CommonTools.notes import Note
from CommonTools.notes.editor import NoteEditor
from .player_panel import PlayerItem
from .player_panel import PlayerSelectionWidget


class DialogCreateNote(QDialog):
    def __init__(self, note: Optional[Note] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Note")
        self.resize(800, 600)
        note = note or Note()
        
        self.editor = NoteEditor()
        self.editor.set_note(note)
        
        self.box = QVBoxLayout(self)
        self.box.addWidget(self.editor)
        
        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        self.btns.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.box.addWidget(self.btns, alignment=Qt.AlignmentFlag.AlignHCenter)
        
    @classmethod
    def request(cls, parent, note: Optional[Note] = None):
        dialog = DialogCreateNote(note, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.editor.get_note()
        return None
        
        