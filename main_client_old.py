import sys

from PySide6.QtWidgets import QApplication

from ClientTools.ui import GameTable

# noinspection PyUnresolvedReferences
import assets_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = GameTable()
    window.show()
    
    sys.exit(app.exec())
