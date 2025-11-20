import sys

from PySide6.QtWidgets import QApplication

from ServerTools.ui.master_window import MasterGameTable

# noinspection PyUnresolvedReferences
import assets_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MasterGameTable()
    window.show()
    
    sys.exit(app.exec())