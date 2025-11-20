import sys
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='pkg_resources')

from PySide6.QtWidgets import QApplication

from CommonTools.dialogRun import RunDialog
from ServerTools.ui.master_window import MasterGameTable
from ClientTools.ui.client_window import PlayerGameTable


# noinspection PyUnresolvedReferences
import assets_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = None
    match RunDialog.getWhatRunner(app.quit):
        case "Master":
            window = MasterGameTable()
        case "Player":
            window = PlayerGameTable()
    if window is not None:
        window.show()
        sys.exit(app.exec())