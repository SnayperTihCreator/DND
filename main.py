import os
import sys
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='pkg_resources')

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat

from CommonTools.dialogRun import RunDialog
from ServerTools.ui.master_window import MasterGameTable
from ClientTools.ui.client_window import PlayerGameTable
from PrintManager import PrintManager


# noinspection PyUnresolvedReferences
import assets_rc
# noinspection PyUnresolvedReferences
import log

sys.argv += ['--ignore-certificate-errors', '--ignore-ssl-errors']
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu-shader-disk-cache"

if __name__ == "__main__":
    with PrintManager() as pm:
        pm.show_caller_info(True)
        
        format = QSurfaceFormat()
        format.setAlphaBufferSize(8)  # Просим 8 бит для прозрачности
        format.setDepthBufferSize(24)  # 24 бита для глубины (чтобы 3D не глючило)
        format.setSamples(4)  # Сглаживание (красивые края)
        QSurfaceFormat.setDefaultFormat(format)
        
        QApplication.setApplicationName("Dnd Table")
        QApplication.setApplicationVersion("1.0.0")
        QApplication.setOrganizationName("SnayperTihCreator")
        QApplication.setApplicationDisplayName("Dnd Virtual Table")
        app = QApplication(sys.argv)
        
        window = None
        match RunDialog.getWhatRunner(app.quit):
            case ["master", login]:
                window = MasterGameTable(login)
            case ["player", login]:
                window = PlayerGameTable(login)
        if window is not None:
            window.show()
            sys.exit(app.exec())