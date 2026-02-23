from pathlib import Path

import json5
from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QMessageBox, \
    QMenu, QInputDialog, QFileDialog, QWidget, QGridLayout
from attrs import asdict

from CommonTools.notes import Note


class NoteBookDock(QDockWidget):
    requestSend = Signal(object)
    requestEdit = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__("Книга записок", parent)
        self.notes: list[Note] = []
        
        self.central = QWidget()
        self.box = QVBoxLayout(self.central)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Найти...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter)
        self.box.addWidget(self.search_bar)
        
        self.notes_list = QListWidget()
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self._menu)
        self.notes_list.doubleClicked.connect(self._on_context_menu)
        self.box.addWidget(self.notes_list)
        
        self.btns = QGridLayout()
        
        self.btn_add = QPushButton("New")
        self.btn_add.clicked.connect(self._add_note)
        self.btns.addWidget(self.btn_add, 0, 0)
        
        self.btn_imp = QPushButton("Import")
        self.btn_imp.clicked.connect(self._import_note)
        self.btns.addWidget(self.btn_imp, 0, 1)
        
        self.btn_load_book = QPushButton("Load book")
        self.btn_load_book.clicked.connect(self._load_book)
        self.btns.addWidget(self.btn_load_book, 1, 0)
        
        self.btn_save_book = QPushButton("Save book")
        self.btn_save_book.clicked.connect(self._save_book)
        self.btns.addWidget(self.btn_save_book, 1, 1)
        
        self.box.addLayout(self.btns)
        self.setWidget(self.central)
    
    def _on_context_menu(self, idx: QModelIndex):
        self.requestSend.emit(self.notes[idx.row()])
    
    def _filter(self, text):
        for i in range(self.notes_list.count()):
            self.notes_list.item(i).setHidden(text.lower() not in self.notes_list.item(i).text().lower())
    
    def _menu(self, pos):
        item = self.notes_list.itemAt(pos)
        if not item: return
        idx = self.notes_list.row(item)
        
        menu = QMenu()
        menu.addAction("Edit", lambda: self.requestEdit.emit(self.notes[idx]))
        menu.addAction("Export", lambda: self._export_note(idx))
        menu.addAction("Delete", lambda: self._delete_note(idx))
        menu.exec(self.notes_list.mapToGlobal(pos))
    
    def _add_note(self):
        text, ok = QInputDialog.getText(self, "Новая", "Заголовок")
        if not (text and ok): return
        
        note = Note(title=text)
        self.notes.append(note)
        self.notes_list.addItem(note.title)
        self.requestEdit.emit(note)
    
    def _delete_note(self, idx):
        if QMessageBox.question(self, "", "Удалить?") == QMessageBox.StandardButton.Yes:
            self.notes.pop(idx)
            self.notes_list.takeItem(idx)
    
    def _export_note(self, idx):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", f"{self.notes[idx].title}.json", "JSON(*.json, *.json5)")
        if not path: return
        
        with open(path, "w", encoding="utf-8") as file:
            json5.dump(asdict(self.notes[idx]), file, ensure_ascii=False, indent=4)
    
    def _import_note(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт", "../components", "JSON(*.json, *.json5)")
        if not path: return
        
        with open(path, "r", encoding="utf-8") as file:
            note = json5.load(file, object_hook=Note)
            self.notes.append(note)
            self.notes_list.addItem(note)
    
    def _save_book(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить книгу", "my_book.json", "JSON (*.json)")
        if not path: return
        self.save_to_path(path)
    
    def _load_book(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть книгу", "../components", "JSON (*.json)")
        if not path: return
        self.load_from_path(path)
    
    def save_to_path(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json5.dump([asdict(note) for note in self.notes], file, ensure_ascii=False, indent=4)
    
    def load_from_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                self.notes = [Note(**data) for data in json5.load(file)]
                self.notes_list.clear()
                [self.notes_list.addItem(note.title) for note in self.notes]
        except Exception as e:
            print(e)
