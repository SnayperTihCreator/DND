from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QTextBrowser


class AutoResizingTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textChanged.connect(self.updateGeometry)
    
    def sizeHint(self):
        return QSize(self.width(), self.fit_height())
    
    def fit_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        height = doc.size().height()
        height += self.frameWidth() * 2
        return int(height + 5)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()