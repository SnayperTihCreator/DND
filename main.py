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
    QApplication.setApplicationName("Dnd Table")
    QApplication.setApplicationVersion("1.0.0")
    QApplication.setOrganizationName("SnayperTihCreator")
    QApplication.setApplicationDisplayName("Dnd Virtual Table")
    app = QApplication(sys.argv)
    
    window = None
    match RunDialog.getWhatRunner(app.quit):
        case ["Master", login]:
            window = MasterGameTable(login)
        case ["Player", login]:
            window = PlayerGameTable(login)
    if window is not None:
        window.show()
        sys.exit(app.exec())