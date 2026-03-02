from pydantic import Field

from .core import BaseMessage, BaseActionType


class ImageActionType(BaseActionType):
    NAME_REQUEST = "image", "name", "data"
    
    SEND_DIRECT = "image", "direct", "data"
    SEND_COMPRESS = "image", "compress", "data"
    
    SEND_CHUNK_START = "image", "chunk", "start"
    SEND_CHUNK = "image", "chunk", "data"
    SEND_CHUNK_END = "image", "chunk", "end"


class ImageMessage(BaseMessage):
    uid: str = Field("")


class ImageNameRequest(ImageMessage, type=ImageActionType.NAME_REQUEST):
    name: str


class ImageSendDirect(ImageMessage, type=ImageActionType.SEND_DIRECT):
    name: str
    size: int
    data: str
    suffix: str


class ImageSendCompress(ImageMessage, type=ImageActionType.SEND_COMPRESS):
    name: str
    osize: int
    csize: int
    quality: int
    data: str = Field(repr=False)
    suffix: str


class ImageMessageChunk(ImageMessage):
    session_id: str


class ImageSendChunkStart(ImageMessageChunk, type=ImageActionType.SEND_CHUNK_START):
    name: str
    total_chunks: int
    total_size: int
    quality: int
    chunk_size: int
    suffix: str


class ImageSendChunk(ImageMessageChunk, type=ImageActionType.SEND_CHUNK):
    chunk_index: int
    data: str


class ImageSendChunkEnd(ImageMessageChunk, type=ImageActionType.SEND_CHUNK_END):
    pass


__all__ = ["ImageActionType",
           
           "ImageNameRequest",
           
           "ImageSendDirect", "ImageSendCompress",
           
           "ImageSendChunkStart", "ImageSendChunk", "ImageSendChunkEnd"]
