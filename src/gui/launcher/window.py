from enum import IntEnum, auto

from PySide6.QtWidgets import QMainWindow, QLabel

from dnd_metadata import version
from uic.launcher_ui import Ui_MainWindow
from CommonTools.updater_manager import UpdateManager
import log


class PageEnum(IntEnum):
    SCANNER_PAGE = 0
    DM_PAGE = auto()


class LauncherWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        log.setup_logging()
        super().__init__()
        self.setupUi(self)
        self.statusBar().addWidget(QLabel(f"Version: {version}"))
        self.scannerPage.launcher = self
        self.dmPage.launcher = self
        
        self.updater = UpdateManager(self)
        self.action_update.triggered.connect(self._check_update)
    
    def _check_update(self):
        self.updater.check_for_updates(False)
    
    def closeEvent(self, event):
        self.updater.stop_download_thread()
        return super().closeEvent(event)
