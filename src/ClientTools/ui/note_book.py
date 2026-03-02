from pathlib import Path

import json5
from attrs import asdict
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLineEdit, QListWidget, QSplitter
from PySide6.QtCore import Qt

from CommonTools.notes import NotePreviewWidget, Note


class NoteBookDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Архив заметок", parent)
        self.notes: list[Note] = []
        self.backup_path = Path(".cache")/"notes_backup.json"
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.central = QWidget()
        self.box = QVBoxLayout(self.central)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Найти...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter)
        self.box.addWidget(self.search_bar)
        
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        
        self.notes_list = QListWidget()
        self.notes_list.currentRowChanged.connect(self._show_note)
        self.splitter.addWidget(self.notes_list)
        
        self.preview = NotePreviewWidget()
        self.splitter.addWidget(self.preview)
        self.preview.hide()
        self.box.addWidget(self.splitter)
        
        self.setWidget(self.central)
        self.load_backup()
    
    def add_note(self, note: Note):
        self.notes.insert(0, note)
        self.notes_list.insertItem(0, note.title)
        self.save_backup()
    
    def _show_note(self, idx):
        if not (0 <= idx < len(self.notes)): return
        self.preview.set_note(self.notes[idx])
        if not self.preview.isVisible():
            self.preview.show()
    
    def _filter(self, text):
        for i in range(self.notes_list.count()):
            self.notes_list.item(i).setHidden(text.lower() not in self.notes_list.item(i).text().lower())
    
    def save_backup(self):
        with open(self.backup_path, "w", encoding="utf-8") as file:
            json5.dump([asdict(note) for note in self.notes], file, ensure_ascii=False, indent=4)
    
    def load_backup(self):
        if self.backup_path.exists():
            try:
                with open(self.backup_path, "r", encoding="utf-8") as file:
                    self.notes = json5.load(file)
                    self.notes_list.clear()
                    [self.notes_list.addItem(note.title) for note in self.notes]
            except Exception:
                pass
