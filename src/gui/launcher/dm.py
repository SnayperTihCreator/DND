import asyncio

from PySide6.QtWidgets import QWidget, QMainWindow

from uic.dm_ui import Ui_Form
from gui.master.master_window import MasterGameTable
import log


class DmPage(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.launcher: QMainWindow = None
        self.win: MasterGameTable = None
        self.checkBoxRemote.toggled.connect(self._change_page)
        self.btnCreate.clicked.connect(self._create_table)
        self.btnConnect.clicked.connect(self._connect_table)
    
    def _change_page(self, status):
        self.pages.setCurrentIndex(int(status))
    
    def _create(self, login, token):
        log.setup_logging("master")
        self.win = MasterGameTable(login, token)
        self.win.show()
        loop = asyncio.get_event_loop()
        loop.call_soon(self.win.start_services)
        self.launcher.close()
    
    def _create_table(self):
        login = self.lineEditLogin.text().strip()
        self._create(login, "")
    
    def _connect_table(self):
        login = self.lineEditLogin.text().strip()
        master_token = self.lineEditMasterToken.text().strip()
        master_ip = self.lineEditIp.text().strip()
        self._create(login, f"{master_ip}|{master_token}")
