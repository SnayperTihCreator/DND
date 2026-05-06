import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QMainWindow, QListWidgetItem

import log
from ClientTools.ui.client_window import PlayerGameTable
from uic.scanner_ui import Ui_Scanner
from CommonTools.core import ServerScanner


class ScannerPage(QWidget, Ui_Scanner):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.launcher: QMainWindow = None
        self.win: PlayerGameTable = None
        
        self.scanner = ServerScanner()
        self.scanner.server_found.connect(self._finder_server)
        self.scanner.scan_finished.connect(self._finished_scanner)
        
        self.listWidgetTables.doubleClicked.connect(self._join_from_list)
        self.btnUpdateTables.clicked.connect(self._start_scanner)
        self.btnConnect.clicked.connect(self._join_manual)
        
        loop = asyncio.get_event_loop()
        loop.call_soon(self._start_scanner)
    
    def _join_from_list(self, item: QListWidgetItem):
        info = item.data(Qt.ItemDataRole.UserRole)
        login = self.lineEditLogin.text().strip()
        self._launch_player(login, info['best_ip'], info['ws_port'])
    
    def _join_manual(self):
        login = self.lineEditLogin.text()
        ip = self.lineEditIp.text().strip()
        port = self.spinPort.value()
        if ip and port:
            self._launch_player(login, ip, port)
    
    def _launch_player(self, login:str, ip: str, port: int):
        log.setup_logging("player")
        self.win = PlayerGameTable(login, ip, port)
        self.win.show()
        loop = asyncio.get_event_loop()
        loop.call_soon(self.win.start_services)
        self.launcher.close()
    
    def _start_scanner(self):
        self.listWidgetTables.clear()
        self.btnUpdateTables.setText("Поиск...")
        self.btnUpdateTables.setDisabled(True)
        asyncio.create_task(self.scanner.scan())
    
    def _finder_server(self, info: dict):
        text = f"{info['name']}  |  {info['best_ip']}:{info['ws_port']}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, info)
        self.listWidgetTables.addItem(item)
    
    def _finished_scanner(self):
        self.btnUpdateTables.setText("Обновить список")
        self.btnUpdateTables.setDisabled(False)