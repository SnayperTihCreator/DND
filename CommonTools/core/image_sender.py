import base64
import os
from typing import Optional
from contextlib import contextmanager
import time
from pathlib import Path


from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from CommonTools.utils import compress_image_to_base64
from CommonTools.messages import *
from .client_data import ClientData


class ImageSender(QObject):
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.client: Optional[ClientData] = None
        
        self.current_session: Optional[str] = None
    
    @contextmanager
    def bind_socket(self, socket: ClientData):
        self.client = socket
        try:
            yield
        finally:
            self.client = None
    
    def send_image(self, path, name):
        if self.client is None:
            self.error_occurred.emit("Не найден сокет")
            return False
        match os.path.getsize(path) / 1024:
            case size if size < 500:
                return self.send_image_direct(path, name, self.client)
            case size if size < 1024:
                return self.send_image_compress(path, name, self.client)
            case _:
                return self.send_image_chunked(path, name, self.client)
        
    def send_image_socket(self, path, name, socket: ClientData):
        if socket is None:
            self.error_occurred.emit("Не найден сокет")
            return False
        match os.path.getsize(path) / 1024:
            case size if size < 500:
                return self.send_image_direct(path, name, socket)
            case size if size < 1024:
                return self.send_image_compress(path, name, socket)
            case _:
                return self.send_image_chunked(path, name, socket)
    
    def send_image_direct(self, path, name, socket: ClientData):
        try:
            with open(path, "rb") as file:
                image_data = base64.b64encode(file.read()).decode("utf-8")
            
            socket.send_msg(ImageSendDirect(
                name=name,
                size=len(image_data),
                data=image_data,
                suffix=Path(path).suffix
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
    
    def send_image_compress(self, path, name, socket, quality=75):
        try:
            image_data, suffix = compress_image_to_base64(path, quality)
            socket.send_msg(ImageSendCompress(
                name=name,
                osize=os.path.getsize(path),
                csize=len(image_data),
                quality=quality,
                data=image_data,
                suffix=suffix
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
    
    def send_image_chunked(self, path, name, socket, quality=60, chunk_size=64 * 1024):
        try:
            image_data, suffix = compress_image_to_base64(path, quality)
            image_data = image_data.encode("utf-8")
            chunks = [image_data[i:i + chunk_size]
                      for i in range(0, len(image_data), chunk_size)]
            current_session = f"session_{int(time.time() * 1000)}"
            socket.send_msg(ImageSendChunkStart(
                session_id=current_session,
                name=name,
                total_chunks=len(chunks),
                total_size=len(image_data),
                quality=quality,
                chunk_size=chunk_size,
                suffix=suffix
            ))
            
            for i, chunk in enumerate(chunks):
                QApplication.processEvents()
                socket.send_msg(ImageSendChunk(
                    session_id=current_session,
                    chunk_index=i,
                    data=chunk.decode("utf-8")
                ))
            
            socket.send_msg(ImageSendChunkEnd(
                session_id=current_session
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
