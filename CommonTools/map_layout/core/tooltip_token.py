from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QTextDocument, QPen, QAbstractTextDocumentLayout, QPalette
from PySide6.QtWidgets import QGraphicsItem

from CommonTools.utils.qrcpath import QRcPath


class ToolTipToken(QGraphicsItem):
    bg_color = QColor.fromRgb(30, 30, 30, 230)
    text_color = QColor.fromRgb(255, 255, 255)
    border_color = QColor.fromRgb(100, 100, 100)
    padding = 8
    font = QFont("Arial", 12)
    max_width = 250
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        
        self.doc = QTextDocument()
        self.doc.setDefaultFont(self.font)
        cssPath = QRcPath(":/css/tooltip.css")
        self.doc.setDefaultStyleSheet(cssPath.read_text())
        self.setZValue(10000)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setToolText(text)
    
    def setToolText(self, text):
        self.doc.setHtml(text)
        self.doc.setTextWidth(self.max_width)
        ideal_width = self.doc.idealWidth()
        self.content_width = min(self.max_width, ideal_width)
        self.doc.setTextWidth(self.content_width)
        self.content_height = self.doc.size().height()
        self.rect_w = self.content_width + self.padding * 2
        self.rect_h = self.content_height + self.padding * 2
        self.update()
    
    def boundingRect(self):
        return QRectF(0, 0, self.rect_w, self.rect_h)
    
    def paint(self, painter, option, widget=None):
        painter.setBrush(self.bg_color)
        painter.setPen(QPen(self.border_color, 1))
        painter.drawRoundedRect(self.boundingRect(), 6, 6)
        
        painter.save()
        painter.translate(self.padding, self.padding)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.doc.documentLayout().draw(painter, ctx)
        painter.restore()
