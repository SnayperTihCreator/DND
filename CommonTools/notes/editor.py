from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QLineEdit

from .base import Note
from CommonTools.components import AdvancedTextEdit


class NoteEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.box = QVBoxLayout(self)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название")
        self.box.addWidget(self.title_input)
        
        self.bg_spin = QSpinBox()
        self.bg_spin.setRange(1, 15)
        self.bg_spin.setPrefix("Фон ")
        self.bg_spin.valueChanged.connect(self._on_change_bg)
        self.box.addWidget(self.bg_spin)
        
        # Наш новый отдельный компонент
        self.editor = AdvancedTextEdit()
        self.box.addWidget(self.editor)
        
        self._on_change_bg(1)
    
    def _on_change_bg(self, idx):
        self.editor.setFon(f":/letters/{idx}.png")
    
    def get_note(self):
        return Note(self.editor.toHtml(), self.title_input.text(), self.bg_spin.value())


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    editor = NoteEditor()
    editor.show()
    app.exec()
