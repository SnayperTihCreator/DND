import os
import sys
import warnings
import asyncio

import certifi
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat
from qasync import QEventLoop

warnings.filterwarnings("ignore", category=UserWarning, module='pkg_resources')

from CommonTools.ui import LauncherWindow
from PrintManager import PrintManager

os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

# noinspection PyUnresolvedReferences
import assets_rc

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
        
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        launcher = LauncherWindow()
        launcher.show()
        
        with loop:
            loop.run_forever()
