import sys

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from views.maps import Maps

app = QApplication(sys.argv)
view = Maps()

m = view.addMap("main")
m.load(r"C:\Users\MSI\Documents\Python\DND\.cache\main.gif")
m2 = view.addMap("main2")
m2.load(r"C:\Users\MSI\Documents\Python\DND\.cache\h.png")


view.resize(800, 600)
view.show()
app.exec()
