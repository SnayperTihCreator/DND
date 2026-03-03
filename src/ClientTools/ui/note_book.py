import logging
from pathlib import Path

import json5
from attrs import asdict
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLineEdit, QListWidget, QSplitter
from PySide6.QtCore import Qt

from CommonTools.notes import NotePreviewWidget, Note

logger = logging.getLogger(__name__)


class NoteBookDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Архив заметок", parent)
        logger.info("NoteBookDock initialized.")
        self.notes: list[Note] = []
        self.backup_path = Path(".cache") / "notes_backup.json"
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.central = QWidget()
        self.box = QVBoxLayout(self.central)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Find...")
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
        logger.info("Adding new note: '%s'", note.title)
        self.notes.insert(0, note)
        self.notes_list.insertItem(0, note.title)
        self.save_backup()
    
    def _show_note(self, idx):
        if not (0 <= idx < len(self.notes)): return
        note_title = self.notes[idx].title
        logger.debug("Displaying note at index %d: '%s'", idx, note_title)
        self.preview.set_note(self.notes[idx])
        if not self.preview.isVisible():
            self.preview.show()
    
    def _filter(self, text):
        logger.debug("Filtering notes with text: '%s'", text)
        for i in range(self.notes_list.count()):
            self.notes_list.item(i).setHidden(text.lower() not in self.notes_list.item(i).text().lower())
    
    def save_backup(self):
        try:
            with open(self.backup_path, "w", encoding="utf-8") as file:
                json5.dump([asdict(note) for note in self.notes], file, ensure_ascii=False, indent=4)
            logger.debug("Notes backup saved successfully to %s (%d notes).", self.backup_path, len(self.notes))
        except Exception:
            logger.exception("Failed to save notes backup to %s", self.backup_path)
    
    def load_backup(self):
        if self.backup_path.exists():
            try:
                with open(self.backup_path, "r", encoding="utf-8") as file:
                    data = json5.load(file)
                    self.notes = [Note(**note_data) for note_data in data]
                    self.notes_list.clear()
                    [self.notes_list.addItem(note.title) for note in self.notes]
                logger.info("Notes backup loaded from %s. Found %d notes.", self.backup_path, len(self.notes))
            except Exception:
                logger.exception("Failed to load or parse notes backup from %s", self.backup_path)
        else:
            logger.info("No notes backup file found at %s. Starting with a new notebook.", self.backup_path)
