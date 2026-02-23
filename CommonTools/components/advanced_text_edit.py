from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QFontComboBox, QTextEdit, QSpinBox, QLineEdit
from PySide6.QtGui import QFont, QTextCharFormat, QAction, QKeySequence, QColor

from CommonTools.components import ColorButton


class AdvancedTextEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Тулбар
        self.toolbar = QToolBar()
        self.layout.addWidget(self.toolbar)
        
        # Шрифт и размер
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._on_font_select)
        self.toolbar.addWidget(self.font_combo)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 100)
        self.size_spin.setValue(14)
        self.size_spin.valueChanged.connect(self._on_font_size)
        self.toolbar.addWidget(self.size_spin)
        
        self.toolbar.addSeparator()
        
        # Кнопки форматирования
        self.act_bold = self._add_action("B", QKeySequence.StandardKey.Bold, self._on_select_bold, bold=True)
        self.act_italic = self._add_action("I", QKeySequence.StandardKey.Italic, self._on_select_italic, italic=True)
        self.act_under = self._add_action("U", QKeySequence.StandardKey.Underline, self._on_select_under,
                                          underline=True)
        self.act_strike = self._add_action("S", None, self._on_select_strike, strike=True)
        
        self.toolbar.addSeparator()
        
        # Цвет
        self.colorBtn = ColorButton()
        self.colorBtn.color_changed.connect(self._on_change_color)
        self.toolbar.addWidget(self.colorBtn)
        
        # Текстовое поле
        self.textEdit = QTextEdit()
        self.textEdit.currentCharFormatChanged.connect(self.update_format)
        self.layout.addWidget(self.textEdit)
    
    def _add_action(self, text, shortcut, callback, bold=False, italic=False, underline=False, strike=False):
        action = QAction(text, self)
        action.setCheckable(True)
        if shortcut: action.setShortcut(shortcut)
        font = QFont("Arial", 12)
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        font.setStrikeOut(strike)
        action.setFont(font)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
        return action
    
    def setFon(self, image_path):
        """Метод для установки фона и цвета текста по умолчанию"""
        self.textEdit.setStyleSheet(f"""
            QTextEdit {{
                border-image: url({image_path}) 0 0 0 0 stretch stretch;
                padding: 1px;
                font-size: {self.size_spin.value()}pt;
            }}
        """)
    
    def toHtml(self):
        return self.textEdit.toHtml()
    
    def setHtml(self, html):
        self.textEdit.setHtml(html)
    
    def _on_change_color(self, color):
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self.merge_format_selection(fmt)
        self.textEdit.setFocus()
    
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
        self.colorBtn.setColor(currentFmt.foreground().color())
        
        font = currentFmt.font()
        if currentFmt.fontPointSize() > 0:
            self.size_spin.setValue(int(currentFmt.fontPointSize()))
        self.font_combo.setCurrentFont(font)
        self.blocking(False)
    
    def blocking(self, state):
        for w in [self.font_combo, self.size_spin, self.colorBtn]: w.blockSignals(state)
        for a in [self.act_bold, self.act_italic, self.act_under, self.act_strike]: a.blockSignals(state)
