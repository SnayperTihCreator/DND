import sys

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication


def restart_app():
    """Перезапускает текущее приложение."""
    QApplication.quit()
    QProcess.startDetached(sys.executable, sys.argv)