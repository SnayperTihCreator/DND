import sys

from PySide6.QtWidgets import QApplication

from ClientTools.ui.client_window import PlayerGameTable

# noinspection PyUnresolvedReferences
import assets_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = PlayerGameTable()
    window.show()
    
    sys.exit(app.exec())