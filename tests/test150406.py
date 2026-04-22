import sys

# noinspection PyUnresolvedReferences
import assets_rc

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from views.maps import Maps, ModeMap

app = QApplication(sys.argv)
view = Maps()

m = view.addMap("main")
m.load(r"C:\Users\MSI\Documents\Python\DND\.cache\main.gif")
m.provider.fog.clear()
m2 = view.addMap("main2")
m2.load(r"C:\Users\MSI\Documents\Python\DND\.cache\h.png")
m3 = view.addMap("main3")
m3.load("./100x100.paint")
m3.painter.set_width(1)
m3.painter.set_color(QColor("#f0dae"))
# m3.painter.set_eraser(True)
# m3.provider.fog.set_eraser(False)
m3.setMode(ModeMap.FOG_MAP)


view.resize(800, 600)
view.show()
app.exec()
