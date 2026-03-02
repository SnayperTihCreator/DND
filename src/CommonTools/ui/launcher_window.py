import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel,
                               QTabWidget, QListWidgetItem)

from ClientTools.ui.client_window import PlayerGameTable
from CommonTools.core import ServerScanner
from CommonTools.updater_manager import UpdateManager
# --- Импортируй свои классы ---
from ServerTools.ui.master_window import MasterGameTable


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D&D Launcher")
        self.resize(450, 500)
        
        # --- СОЗДАЕМ UpdateManager ---
        self.updater = UpdateManager(self)
        
        self.master_window = None
        self.player_window = None
        
        # Создаем центральный виджет, который будет содержать и табы, и кнопку
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # --- (дальше твои табы без изменений) ---
        self.join_tab = QWidget()
        self._setup_join_ui()
        tabs.addTab(self.join_tab, "Найти игру")
        
        self.create_tab = QWidget()
        self._setup_create_ui()
        tabs.addTab(self.create_tab, "Создать стол")
        
        # --- ДОБАВЛЯЕМ КНОПКУ ОБНОВЛЕНИЯ ВНИЗ ---
        self.btn_update = QPushButton("Проверить обновления")
        self.btn_update.clicked.connect(lambda: self.updater.check_for_updates(False))
        main_layout.addWidget(self.btn_update)
        
        # Наш сканер
        self.scanner = ServerScanner()
        self.scanner.server_found.connect(self._add_server_to_list)
        self.scanner.scan_finished.connect(self._on_scan_finished)
        
        # Запускаем сканирование при старте
        loop = asyncio.get_event_loop()
        loop.call_soon(self._start_scan)
    
    def _setup_join_ui(self):
        layout = QVBoxLayout(self.join_tab)
        layout.addWidget(QLabel("Доступные столы в сети (LAN/VPN):"))
        
        self.server_list = QListWidget()
        self.server_list.itemDoubleClicked.connect(self._join_from_list)
        layout.addWidget(self.server_list)
        
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self._start_scan)
        layout.addWidget(self.btn_refresh)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("Или подключиться напрямую:"))
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP адрес мастера")
        layout.addWidget(self.ip_input)
        
        self.port_input = QLineEdit("8765")
        self.port_input.setPlaceholderText("Порт")
        layout.addWidget(self.port_input)
        
        btn_connect = QPushButton("Подключиться вручную")
        btn_connect.clicked.connect(self._join_manual)
        layout.addWidget(btn_connect)
        
        self.login_input_client = QLineEdit()
        self.login_input_client.setText("DndGame")
        layout.addWidget(self.login_input_client)
    
    def _setup_create_ui(self):
        layout = QVBoxLayout(self.create_tab)
        self.login_input = QLineEdit("DungeonMaster")
        layout.addWidget(QLabel("Ваш никнейм (Мастер):"))
        layout.addWidget(self.login_input)
        
        btn_create = QPushButton("Создать стол")
        btn_create.clicked.connect(self._launch_master)
        layout.addWidget(btn_create)
        layout.addStretch()
    
    def _start_scan(self):
        self.server_list.clear()
        self.btn_refresh.setText("Поиск...")
        self.btn_refresh.setDisabled(True)
        asyncio.create_task(self.scanner.scan())
    
    def _on_scan_finished(self):
        self.btn_refresh.setText("Обновить список")
        self.btn_refresh.setDisabled(False)
    
    def _add_server_to_list(self, info: dict):
        text = f"{info['name']}  |  {info['ip']}:{info['ws_port']}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, info)  # Сохраняем данные для подключения
        self.server_list.addItem(item)
    
    def _launch_master(self):
        login = self.login_input.text()
        self.master_window = MasterGameTable(login)
        self.master_window.show()
        loop = asyncio.get_event_loop()
        loop.call_soon(self.master_window.start_services)
        self.close()  # Закрываем лаунчер
    
    def _join_from_list(self, item: QListWidgetItem):
        info = item.data(Qt.ItemDataRole.UserRole)
        self._launch_player(info['ip'], info['ws_port'])
    
    def _join_manual(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        if ip and port:
            self._launch_player(ip, int(port))
    
    def _launch_player(self, ip: str, port: int):
        self.player_window = PlayerGameTable(login=self.login_input_client.text(), server_ip=ip, server_port=port)
        self.player_window.show()
        loop = asyncio.get_event_loop()
        loop.call_soon(self.player_window.start_services)
        self.close()
    
    def closeEvent(self, event):
        self.updater.stop_download_thread()
        super().closeEvent(event)
