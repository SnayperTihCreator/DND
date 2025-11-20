import textwrap
import json5
from PySide6.QtCore import QUrl, Signal, QObject, QByteArray
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket

from ClientTools.core.image_sender import ImageSender
from ClientTools.core.image_receiver import ImageReceiver, ReceivedImage
from CommonTools.messages import *


class WebSocketClient(QObject):
    """Унифицированный WebSocket клиент для общения с сервером"""
    
    # Сигналы для UI
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str)
    b_message_received = Signal(QByteArray)
    error_occurred = Signal(str)
    
    # Сигналы для отправки изображений
    send_progress = Signal(int)
    send_complete = Signal(str)
    send_error = Signal(str)
    
    # Сигналы для приема изображений
    image_received = Signal(ReceivedImage)
    chunk_progress = Signal(str, int)
    chunk_started = Signal(str, int)
    receive_error = Signal(str)
    
    def __init__(self, max_size=10 * 1024 * 1024, parent=None):
        super().__init__(parent)
        self.websocket = QWebSocket()
        self.websocket.setMaxAllowedIncomingMessageSize(max_size)
        
        # Инициализация менеджеров отправки и приема изображений
        self.image_sender = ImageSender(self)
        self.image_receiver = ImageReceiver()
        
        self._setup_connections()
    
    def _setup_connections(self):
        """Настройка всех соединений между компонентами"""
        # Соединения WebSocket
        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_text_message_received)
        self.websocket.errorOccurred.connect(self.on_error)
        
        # Колбэки для отправки изображений
        self.image_sender.on_progress = lambda progress: self.send_progress.emit(progress)
        self.image_sender.on_complete = lambda msg: self.send_complete.emit(msg)
        self.image_sender.on_error = lambda error: self.send_error.emit(error)
        
        # Сигналы для приема изображений
        self.image_receiver.image_received.connect(self.image_received)
        self.image_receiver.chunk_progress.connect(self.chunk_progress)
        self.image_receiver.chunk_started.connect(self._handle_chunk_started)
        self.image_receiver.error_occurred.connect(self.receive_error)
    
    def _handle_chunk_started(self, session_id: str, total_chunks):
        """Обработка начала чанковой передачи - отправка ACK подтверждения"""
        self.chunk_started.emit(session_id, total_chunks)
        
        return self.answer(ImageSendChunkAck(
            session_id=session_id,
            status="ready",
            msg="Готов к приему чанков"
        ))
    
    def connect_to_server(self, url):
        """Подключение к WebSocket серверу"""
        self.websocket.open(QUrl(url))
    
    def disconnect_from_server(self):
        """Отключение от сервера"""
        self.websocket.close()
    
    def send_message(self, msg: str | bytes):
        """Отправка сообщения на сервер (текст или бинарные данные)"""
        if self.websocket.state() == QAbstractSocket.SocketState.ConnectedState:
            if isinstance(msg, str):
                self.websocket.sendTextMessage(msg)
                return True
            elif isinstance(msg, bytes):
                self.websocket.sendBinaryMessage(msg)
                return True
        return False
    
    def send_image(self, image_path, name):
        """Отправка изображения через менеджер отправки"""
        return self.image_sender.send_image(image_path, name)
    
    def set_receive_callback(self, callback):
        """Установка callback для обработки входящих изображений"""
        self.image_receiver.set_callback(callback)
    
    def answer(self, msg):
        """Отправка структурированного сообщения через сериализацию"""
        request = msg.to_dict()
        return self.send_message(json5.dumps(request, ensure_ascii=False))
    
    def on_connected(self):
        """Обработчик успешного подключения к серверу"""
        print("Connected to server")
        self.connected.emit()
    
    def on_disconnected(self):
        """Обработчик отключения от сервера"""
        print("Disconnected from server")
        self.disconnected.emit()
    
    def on_text_message_received(self, msg_raw: str):
        """Обработчик получения текстового сообщения"""
        print(f"📨 Message received: {textwrap.shorten(msg_raw, 100)}")
        msg = BaseMessage.from_str(msg_raw)
        try:
            # Обработка ACK для отправки изображений
            if msg.type == ImageActionType.SEND_CHUNK_ACK:
                self.image_sender.handle_chunk_ack(msg)
                return
        
        except (ValueError, AttributeError):
            pass
        try:
            # Пробуем обработать через менеджер приема изображений
            if self.image_receiver.handle_message(msg):
                pass
            else:
                self.message_received.emit(msg_raw)
        
        except Exception as e:
            error_msg = f"❌ Ошибка обработки входящего сообщения: {e}"
            print(error_msg)
            self.receive_error.emit(error_msg)
        
    def on_error(self, error):
        """Обработчик ошибок WebSocket"""
        error_message = f"WebSocket error: {error}"
        print(error_message)
        self.error_occurred.emit(error_message)
    
    def is_connected(self):
        """Проверка состояния подключения"""
        return self.websocket.state() == QAbstractSocket.SocketState.ConnectedState
    
    def get_receive_progress(self, session_id: str):
        """Получение прогресса приема по сессии"""
        return self.image_receiver.get_session_progress(session_id)
    
    def get_active_receive_sessions(self):
        """Получение активных сессий приема"""
        return self.image_receiver.get_active_sessions()