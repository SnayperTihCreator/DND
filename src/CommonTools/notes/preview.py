from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from .base import Note


class NotePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QTextBrowser()
        self.browser.setFrameStyle(0)
        self.layout.addWidget(self.browser)
    
    def set_note(self, note: Note):
        bg_path = f":/letters/{note.bg_index}.png"
        
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background-image: url({bg_path});
                background-repeat: no-repeat;
                background-position: center;
                border: none;
                font-size: 14px;
            }}
        """)
        
        full_html = f"<h2 style='text-align: center;'>{note.title}</h2><hr>{note.content}"
        self.browser.setHtml(full_html)
