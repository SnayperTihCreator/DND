from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QFontComboBox, QTextEdit, QSpinBox, QLineEdit
from PySide6.QtGui import QFont, QTextCharFormat, QAction, QKeySequence, QImage
from PySide6.QtCore import Qt

from .base import Note


class NoteEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(0, 0, 0, 0)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название")
        self.box.addWidget(self.title_input)
        
        self.textEdit = QTextEdit()  # TODO я чет подумал надо еще цвет добавить
        
        self.bg_spin = QSpinBox()
        self.bg_spin.setRange(1, 15)
        self.bg_spin.setValue(1)
        self.bg_spin.setPrefix("Фон ")
        self.bg_spin.valueChanged.connect(self._on_change_bg)
        
        self.box.addWidget(self.bg_spin)
        
        self.toolbar = QToolBar()
        self.box.addWidget(self.toolbar)
        
        self.font_combo = QFontComboBox()
        self.font_combo.setToolTip("Шрифт")
        self.font_combo.currentFontChanged.connect(self._on_font_select)
        self.toolbar.addWidget(self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 100)
        self.size_spin.setValue(14)
        self.size_spin.setToolTip("Размер шрифта")
        self.size_spin.valueChanged.connect(self._on_font_size)
        self.toolbar.addWidget(self.size_spin)
        
        self.toolbar.addSeparator()
        
        self.act_bold = QAction("B", self)
        self.act_bold.setCheckable(True)
        self.act_bold.setShortcut(QKeySequence.StandardKey.Bold)
        self.act_bold.setFont(QFont("Arial", 14, weight=True))
        self.act_bold.triggered.connect(self._on_select_bold)
        self.toolbar.addAction(self.act_bold)
        
        self.act_italic = QAction("I", self)
        self.act_italic.setCheckable(True)
        self.act_italic.setShortcut(QKeySequence.StandardKey.Italic)
        self.act_italic.setFont(QFont("Arial", 14, italic=True))
        self.act_italic.triggered.connect(self._on_select_italic)
        self.toolbar.addAction(self.act_italic)
        
        self.act_under = QAction("U", self)
        self.act_under.setCheckable(True)
        self.act_under.setShortcut(QKeySequence.StandardKey.Underline)
        font = QFont("Arial", 14)
        font.setUnderline(True)
        self.act_under.setFont(font)
        self.act_under.triggered.connect(self._on_select_under)
        self.toolbar.addAction(self.act_under)
        
        self.act_strike = QAction("S", self)
        self.act_strike.setCheckable(True)
        font = QFont("Arial", 14)
        font.setStrikeOut(True)
        self.act_strike.setFont(font)
        self.act_strike.triggered.connect(self._on_select_strike)
        self.toolbar.addAction(self.act_strike)
        
        self.toolbar.addSeparator()
        
        self.textEdit.currentCharFormatChanged.connect(self.update_format)
        
        self.box.addWidget(self.textEdit)
        self._on_change_bg(1)
    
    def _on_change_bg(self, idx):
        img = QImage(f":/letters/{idx}.png")  # TODO поменять размеры и унифицировать до 640*480
        avg_color = img.scaled(1, 1,
                               Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.SmoothTransformation).pixelColor(0, 0)
        
        text_color = "black" if avg_color.lightness() > 128 else "white"
        self.textEdit.setStyleSheet(f"""
            QTextEdit {{
                background-image: url({f":/letters/{idx}.png"});
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                color: {text_color};
                border: 1px solid {text_color};
                font-size: {self.size_spin.value()}pt;
            }}
        """)
    
    def _on_font_select(self, font: QFont):
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def _on_font_size(self, size):
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def _on_select_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.act_bold.isChecked() else QFont.Weight.Normal)
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def _on_select_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.act_italic.isChecked())
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def _on_select_under(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.act_under.isChecked())
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def _on_select_strike(self):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.act_strike.isChecked())
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
    def merge_format_selection(self, format_):
        cursor = self.textEdit.textCursor()
        cursor.mergeCharFormat(format_)
        self.textEdit.mergeCurrentCharFormat(format_)
    
    def update_format(self):
        self.blocking(True)
        
        currentFmt = self.textEdit.currentCharFormat()
        self.act_bold.setChecked(currentFmt.fontWeight() == QFont.Weight.Bold)
        self.act_italic.setChecked(currentFmt.fontItalic())
        self.act_under.setChecked(currentFmt.fontUnderline())
        self.act_strike.setChecked(currentFmt.fontStrikeOut())
        
        font = currentFmt.font()
        if currentFmt.fontPointSize() > 0:
            self.size_spin.setValue(int(currentFmt.fontPointSize()))
        self.font_combo.setCurrentFont(font)
        self.blocking(False)
    
    def blocking(self, state):
        self.font_combo.blockSignals(state)
        self.size_spin.blockSignals(state)
        
        self.act_bold.blockSignals(state)
        self.act_italic.blockSignals(state)
        self.act_under.blockSignals(state)
        self.act_strike.blockSignals(state)
    
    def get_note(self):
        return Note(self.textEdit.toHtml(), self.title_input.text(), self.bg_spin.value())


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    editor = NoteEditor()
    editor.show()
    app.exec()
