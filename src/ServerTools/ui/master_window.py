import asyncio
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF, QTimer
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QMainWindow, QToolBar, QSpinBox, QLabel, QCheckBox, QFileDialog, \
    QGraphicsColorizeEffect, QComboBox
from psygnal import set_async_backend

from CommonTools.map_layout import MapWidget
from CommonTools.notes import Note
from ..core.server_remote import AsyncServerRemote

logger = logging.getLogger(__name__)
logging.getLogger("Qt.js").setLevel(logging.ERROR)

from CommonTools.components import ColorButton, GuidePanel, RouterDescriptor
from CommonTools.updater_manager import UpdateManager
from ServerTools.core.server_socket import AsyncServerBridge
from CommonTools.messages import *
from CommonTools.core import ClientData
from CommonTools.mime import AssetsMime
from ServerTools.components import *
from CommonTools.utils import getImageMIME

from .master_controller import MasterController
from .note_book import NoteBookDock


class MasterGameTable(QMainWindow):
    router = RouterDescriptor()
    
    def __init__(self, login, master_token=""):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowTitle("Виртуальный стол: Мастер")
        self.setWindowIcon(QIcon(":/icons/main.png"))
        
        self.cache_folder = Path("./.cache/server")
        self.cache_folder.mkdir(exist_ok=True, parents=True)
        
        self.players: dict[str, ClientData] = {}
        self.server = AsyncServerRemote(master_token, self.cache_folder) if master_token else AsyncServerBridge(self.cache_folder)
        
        self.server.client_connected.connect(self._handle_connect)
        self.server.client_disconnected.connect(self._handle_disconnect)
        self.server.server_started.connect(self._on_server_ready)
        self.server.error_occurred.connect(self.showErrorMessage)
        
        self.updater = UpdateManager(self)
        
        self.controller = MasterController(self.server)
        self.controller.error.connect(self.showErrorMessage)
        self.setCentralWidget(self.controller)
        
        self.token_panel = TokensPanel()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.token_panel)
        
        self.guide_panel = GuidePanel("https://5e14.ttg.club/", "Справочник", f"Master{login}")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.guide_panel)
        self.guide_panel.hide()
        
        self.player_panel = PlayerPanel()
        self.player_panel.active_change.connect(self._handle_change_freeze)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.player_panel)
        
        self.note_book = NoteBookDock(self)
        self.note_book.requestEdit.connect(self._on_note_edit)
        self.note_book.requestSend.connect(self._on_note_send)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.note_book)
        
        self.topToolBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.topToolBar)
        
        self.create_map_action = self.topToolBar.addAction("Создать карту")
        self.create_map_action.triggered.connect(self._on_action_add_map)
        self.load_bg_action = self.topToolBar.addAction("Загрузить фон")
        self.load_bg_action.triggered.connect(self._on_action_load_bg)
        self.delete_map_action = self.topToolBar.addAction("Удалить карту")
        self.delete_map_action.triggered.connect(self._on_action_delete_map)
        self.save_map_action = self.topToolBar.addAction("Сохранить карту")
        self.active_map_action = self.topToolBar.addAction("Активировать карту")
        self.active_map_action.triggered.connect(self._on_action_active_map)
        self.btn_access_action = self.topToolBar.addAction("🔴 Стол закрыт")
        self.btn_access_action.setCheckable(True)
        self.btn_access_action.triggered.connect(self._toggle_access)
        
        self.bottomToolBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.bottomToolBar)
        
        self.offset_grid_x = QSpinBox(value=0)
        self.offset_grid_x.valueChanged.connect(self._handle_offset_size_change)
        self.offset_grid_y = QSpinBox(value=0)
        self.offset_grid_y.valueChanged.connect(self._handle_offset_size_change)
        
        self.bottomToolBar.addWidget(QLabel("Отступ"))
        self.bottomToolBar.addWidget(self.offset_grid_x)
        self.bottomToolBar.addWidget(self.offset_grid_y)
        self.bottomToolBar.addWidget(QLabel("\t"))
        
        self.size_grid = QSpinBox(value=50)
        self.size_grid.valueChanged.connect(self._handle_offset_size_change)
        
        self.bottomToolBar.addWidget(QLabel("Размер сетки"))
        self.bottomToolBar.addWidget(self.size_grid)
        self.bottomToolBar.addWidget(QLabel("\t"))
        
        self.btnColorGrid = ColorButton(color="#4a4a4a")
        self.btnColorGrid.color_changed.connect(self._handle_change_color)
        self.checkBoxVisibleGrid = QCheckBox("Сетка")
        self.checkBoxVisibleGrid.setChecked(True)
        self.checkBoxVisibleGrid.toggled.connect(self._handle_change_vgrid)
        
        self.bottomToolBar.addWidget(self.btnColorGrid)
        self.bottomToolBar.addWidget(self.checkBoxVisibleGrid)
        
        self.topPaintBar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.topPaintBar)
        
        self.changeDragPaint = self.topPaintBar.addAction("Редактировать туман")
        self.changeDragPaint.triggered.connect(self._on_action_change_drag_paint)
        self.changeDrawErase = self.topPaintBar.addAction("Стирать")
        self.changeDrawErase.triggered.connect(self._on_action_change_erase)
        self.brushSize = QSpinBox(value=50, minimum=1, maximum=10 ** 6, singleStep=1)
        self.topPaintBar.addWidget(self.brushSize)
        self.brushSize.valueChanged.connect(self._on_action_change_size_brush)
        
        self.actionClearFog = self.topPaintBar.addAction("Очистить туман")
        self.actionClearFog.triggered.connect(self._on_action_clear_fog)
        
        self.actionResetFog = self.topPaintBar.addAction("Восстановить туман")
        self.actionResetFog.triggered.connect(self._on_action_reset_fog)
        
        self.controller.tabMaps.currentMapChanged.connect(self._handle_current_map)
        
        self.menu_panels = self.menuBar().addMenu("Панели")
        self.token_panel_action = self.menu_panels.addAction("Показать панель токенов")
        self.token_panel_action.triggered.connect(self.token_panel.show)
        
        self.guide_panel_action = self.menu_panels.addAction("Показать справочник")
        self.guide_panel_action.triggered.connect(self.guide_panel.show)
        
        self.player_panel_action = self.menu_panels.addAction("Показать панель игроков")
        self.player_panel_action.triggered.connect(self.player_panel.show)
        
        self.note_book_action = self.menu_panels.addAction("Показать панель записок")
        self.note_book_action.triggered.connect(self.note_book.show)
        
        self.menu_updater = self.menuBar().addMenu("Обновления")
        self.check_update_action = self.menu_updater.addAction("Проверить наличие обновлений")
        self.check_update_action.triggered.connect(self._on_action_check_update)
        
        self._deactivate_control()
    
    def start_services(self):
        asyncio.create_task(self._start())
    
    async def _start(self):
        backend = set_async_backend("asyncio")
        
        await backend.running.wait()
        self.server.message_handled.connect(self._handle_message)
        self.server.start_server()
    
    def _on_note_send(self, note: Note):
        status, players = DialogPreviewSend.request(self, note, self.player_panel.getAllPlayers())
        if not status: return
        
        msg = ClientNoteMsg(title=note.title, content=note.content, idx_bg=note.bg_index)
        for uid in players:
            self.server.answer(uid, msg)
    
    def _toggle_access(self, checked: bool):
        """Слот для кнопки открытия/закрытия стола"""
        self.server.set_access(checked)
        self.btn_access_action.setText("🟢 Стол открыт" if checked else "🔴 Стол закрыт")
    
    def _on_server_ready(self, ws_port: int, http_port: int):
        self.setWindowTitle(f"Мастер Стол | Порт: {ws_port}/{http_port}")
        self.statusBar().showMessage(f"Сервер запущен. Порт для игроков: {ws_port}", 5000)
    
    def _on_note_edit(self, note: Note):
        note2 = DialogCreateNote.request(self, note)
        
        if note2 is not None:
            note.copy_data(note2)
            self.note_book.save_to_path(".cache/notes_library.json5")
    
    def applyErrorEffect(self):
        colorize = QGraphicsColorizeEffect(self)
        colorize.setColor(QColor("#f00"))
        
        self.statusBar().setGraphicsEffect(colorize)
    
    def resetEffect(self):
        self.statusBar().setGraphicsEffect(None)
    
    def showErrorMessage(self, msg: str):
        self.applyErrorEffect()
        self.statusBar().showMessage(msg, 2000)
        logger.error(msg)
        QTimer.singleShot(2000, self.resetEffect)
    
    def _on_action_check_update(self):
        self.updater.check_for_updates(False)
    
    def _on_action_add_map(self):
        if self.controller.tabMaps.isEmpty():
            name, visible = "main", True
        else:
            name, visible = DialogCreateMap.getNameAndVisible(
                "Создать карту",
                "Дайте имя карте и будет ли видна карта игрокам")
        if name is not None:
            self.controller.addMap(name, visible)
        self._handle_current_map(name)
    
    def _on_action_delete_map(self):
        if self.controller.tabMaps.isEmpty():
            return
        self.controller.removeActiveMap()
    
    def _on_action_load_bg(self):
        if not (name := self.controller.tabMaps.getActiveNameMap()):
            return
        path, _ = QFileDialog.getOpenFileName(self, "Выберете фон", ".", "Image(*.png *.jpg *.gif)")
        if not path: return
        
        # TODO Добавить норм фильтр
        # path2 = validate_and_resize_image(path, self.assets, max_size=4096)
        # if not path2:
        #     QMessageBox.critical(self, "Ошибка", "Не удалось обработать изображение.")
        #     return
        
        mime = AssetsMime(category="map-fon", filename=name)
        filename = self.server.loadTo(path)
        self.controller.register_image(name, path)
        self.controller.tabMaps.load_map(name, path)
        self.server.broadcast(SystemResourceAvailable(filename=filename))
        self.server.broadcast(MapLoadBackground(mime=mime, filename=filename))
        self._handle_current_map(name)
    
    def closeEvent(self, event):
        self.updater.stop_download_thread()
        self.server.stop_server()
        super().closeEvent(event)
    
    def _on_action_active_map(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            self.controller.activeMap(name)
    
    def _on_action_change_drag_paint(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.setFogMode(not mWidget.isActiveFogMode(), mWidget.isRevealFogMode())
            self._handle_change_state_fog(mWidget)
    
    def _on_action_change_erase(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.setFogMode(mWidget.isActiveFogMode(), not mWidget.isRevealFogMode())
            self._handle_change_state_fog(mWidget)
    
    def _on_action_change_size_brush(self, value):
        self.controller.tabMaps.call_all_method("setFogBrushSize", value)
    
    def _on_action_clear_fog(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.clearFog()
    
    def _on_action_reset_fog(self):
        if name := self.controller.tabMaps.getActiveNameMap():
            mWidget = self.controller.tabMaps.getMap(name)
            mWidget.resetFog()
    
    def _handle_change_state_fog(self, mWidget: MapWidget):
        if mWidget.isActiveFogMode():
            self.changeDragPaint.setText("Перемещение токенов")
            self.changeDrawErase.setDisabled(False)
            self.brushSize.setDisabled(False)
        else:
            self.changeDragPaint.setText("Редактирование тумана")
            self.changeDrawErase.setDisabled(True)
            self.brushSize.setDisabled(True)
        
        if mWidget.isRevealFogMode():
            self.changeDrawErase.setText("Стирать")
        else:
            self.changeDrawErase.setText("Рисовать")
    
    def _handle_offset_size_change(self, *_):
        offset = QPoint(self.offset_grid_x.value(), self.offset_grid_y.value())
        size = self.size_grid.value()
        self.controller.tabMaps.call_all_method("setOffsetSize", offset, size)
        self.server.broadcast(MapGridData(offset=offset.toTuple(), size=size))
    
    def _handle_change_freeze(self, uid, state):
        logger.info(f"Изменения состояния заморозки у {uid}:{state}")
        self.server.answer(uid, MapFreezePlayer(freeze=state))
    
    @staticmethod
    def _handle_connect(uid):
        logger.info(f"Клиент подключен с uid: {uid}")
    
    def _handle_change_color(self, color):
        self.controller.tabMaps.call_all_method("setColorGrid", color)
    
    def _handle_change_vgrid(self, visible):
        self.controller.tabMaps.call_all_method("setVisibleGrid", visible)
    
    def _handle_disconnect(self, uid):
        self.players.pop(uid, None)
        self.controller.update_player_list(self.players)
        self.player_panel.removePlayer(uid)
        self.server.broadcast(ClientRemovePlayer(uid=uid), uid)
        logger.info(f"[SUCCESS] Клиент отключен с uid: {uid}")
    
    async def _handle_message(self, uid, msg: BaseMessage):
        if await self.controller.handle_message(msg): return
        
        if await self.router(uid, msg): return
        
        logger.info("Не обработанное сообщение: %s - %s", msg.type, msg)
    
    @router.handler(ClientActionType.START_PLAYER)
    def _action_add_player(self, uid_answer: str, msg: ClientStartPlayer):
        self.server.answer(uid_answer, msg)
        self.server.clients[uid_answer].iname = msg.iname
        self.server.broadcast(ClientAddPlayer(uid=uid_answer, name=msg.name, cls=msg.cls, iname=msg.iname), uid_answer)
        for uid, client in self.server.clients.items():
            if client.is_playing and uid_answer != uid:
                self.server.answer(uid_answer, ClientAddPlayer(
                    uid=uid, name=client.name, cls=client.cls, iname=client.iname
                ))
        self.players[uid_answer] = self.server.clients[uid_answer]
        self.controller.update_player_list(self.players)
        if msg.iname and (img := self.controller.getImage(msg.iname)):
            imageName = getImageMIME(f"player:{msg.name}:{msg.cls}:{uid_answer}")
            self.controller.register_image(imageName, img)
        self.player_panel.addPlayer(uid_answer, msg.name, msg.cls)
        return True
    
    @router.handler(MapActionType.MAPS_ALL_DATA)
    def _action_get_all_data(self, uid, _: GetAllMaps):
        self.controller.sync_client_data(uid)
    
    @router.handler(MapActionType.PLAYER_MOVED)
    def _handle_player_moved(self, uid, msg: MapPlayerMoved):
        token = self.controller.players_map[uid]
        token.move_to(QPointF(msg.pos[0], msg.pos[1]))
    
    @router.handler(ImageActionType.NAME_REQUEST)
    def _handle_name_map(self, uid, msg: ImageNameRequest):
        if file_path := self.controller.getImage(msg.name):
            # Получаем URL и шлем ответ
            filename = Path(file_path).name
            # url = self.server.get_file_url(filename)
            
            # Тебе нужно сообщение, которое вернет URL. Например:
            # ImageUrlResponse(name=msg.name, url=url)
            # self.server.answer(uid, ImageUrlResponse(name=msg.name, url=url))
            
            # Если такой ответ есть, можно раскомментировать. Пока заглушка:
            logger.info(f"Отправил бы URL {{url}} для {msg.name} клиенту {uid}")
            pass
        else:
            self.server.answer(uid, IgnoreCallback(uid_callback=msg.uid))
    
    def _handle_current_map(self, name: Optional[str]):
        if name is None:
            return
        self._deactivate_control()
        self.load_bg_action.setDisabled(False)
        self.active_map_action.setDisabled(False)
        self.delete_map_action.setDisabled(False)
        name_map = self.controller.tabMaps.getActiveNameMap()
        mWidget = self.controller.tabMaps.getMap(name_map)
        if mWidget and mWidget.file_map:
            self.bottomToolBar.setDisabled(False)
            self.topPaintBar.setDisabled(False)
            self._handle_change_state_fog(mWidget)
    
    def _deactivate_control(self):
        self.topPaintBar.setDisabled(True)
        self.bottomToolBar.setDisabled(True)
        self.topPaintBar.setDisabled(True)
        self.load_bg_action.setDisabled(True)
        self.delete_map_action.setDisabled(True)
        self.save_map_action.setDisabled(True)
        self.active_map_action.setDisabled(True)
