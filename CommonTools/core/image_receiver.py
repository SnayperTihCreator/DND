import base64
from typing import Optional

from attrs import define, field
from PySide6.QtCore import QObject, Signal

from CommonTools.messages import *


@define
class Image:
    image_data: bytes
    strategy: str
    name: str
    suffix: str


@define
class SessionChunk:
    total_chunks: int
    total_size: int
    chunk_size: int
    name: str
    suffix: str
    
    received_chunks: int = field(default=0)
    chunks: list[Optional[bytes]] = field(init=False)
    
    def __attrs_post_init__(self):
        self.chunks = [None] * self.total_chunks


class ImageReceiver(QObject):
    image_received = Signal(object)
    chunk_progress = Signal(str, int)
    
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.active_sessions: dict[str, SessionChunk] = {}
    
    # noinspection PyTypeChecker
    def handle_message(self, msg: BaseMessage):
        match msg.type:
            case ImageActionType.SEND_DIRECT:
                return self._handle_direct(msg)
            case ImageActionType.SEND_COMPRESS:
                return self._handle_compressed(msg)
            case ImageActionType.SEND_CHUNK_START:
                return self._handle_chunk_start(msg)
            case ImageActionType.SEND_CHUNK:
                return self._handle_chunk(msg)
            case ImageActionType.SEND_CHUNK_END:
                return self._handle_chunk_end(msg)
        return False
    
    def _handle_direct(self, msg: ImageSendDirect):
        try:
            image_data = base64.b64decode(msg.data.encode("utf-8"))
            self.image_received.emit(Image(
                image_data,
                "direct",
                msg.name,
                msg.suffix
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
    
    def _handle_compressed(self, msg: ImageSendCompress):
        try:
            image_data = base64.b64decode(msg.data.encode("utf-8"))
            self.image_received.emit(Image(
                image_data,
                "compress",
                msg.name,
                msg.suffix
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
    
    def _handle_chunk_start(self, msg: ImageSendChunkStart):
        try:
            suid = msg.session_id
            self.active_sessions[suid] = SessionChunk(
                msg.total_chunks,
                msg.total_size,
                msg.chunk_size,
                msg.name,
                msg.suffix
            )
            print(f"Start chunked {suid}: {msg.total_chunks}")
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
    
    def _handle_chunk(self, msg: ImageSendChunk):
        try:
            suid = msg.session_id
            if suid not in self.active_sessions:
                print("Session uid not find")
                return
            session = self.active_sessions[suid]
            print(f"chunked {suid}")
            idx = msg.chunk_index
            
            session.chunks[idx] = base64.b64decode(msg.data.encode("utf-8"))
            session.received_chunks += 1
            
            pp = (session.received_chunks / session.total_chunks * 100)
            self.chunk_progress.emit(suid, pp)
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False
        
    def _handle_chunk_end(self, msg: ImageSendChunkEnd):
        try:
            suid = msg.session_id
            if suid not in self.active_sessions:
                print("Session uid not find")
                return
            print(f"End chunked {suid}")
            session = self.active_sessions[suid]
            image_data = b"".join(session.chunks)
            
            self.image_received.emit(Image(
                image_data,
                "chunks",
                session.name,
                session.suffix
            ))
            return True
        except Exception as e:
            msg_error = f"Error: {e}"
            self.error_occurred.emit(msg_error)
            return False