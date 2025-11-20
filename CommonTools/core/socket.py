import json5
from PySide6.QtCore import QObject, Signal

from .client_data import ClientData
from .image_sender import ImageSender
from .image_receiver import ImageReceiver
from CommonTools.messages import BaseMessage


class Socket(QObject):
    message_received = Signal(str)
    image_received = Signal(object)
    chunk_progress = Signal(str, int)
    
    error_occurred = Signal(str)
    
    def __init__(self, socket):
        super().__init__()
        self.socket = socket
        self.client = ClientData("", "", "", socket)
        
        self.image_sender = ImageSender()
        self.image_sender.error_occurred.connect(self.error_occurred.emit)
        
        self.image_receiver = ImageReceiver()
        self.image_receiver.image_received.connect(self.image_received.emit)
        self.image_receiver.chunk_progress.connect(self.chunk_progress.emit)
        self.image_receiver.error_occurred.connect(self.error_occurred.emit)
    
    def send_msg(self, msg: BaseMessage):
        self.socket.sendTextMessage(json5.dumps(msg.to_dict(), ensure_ascii=False))
    
    def send_image(self, path, name):
        self.image_sender.send_image(path, name)
    
