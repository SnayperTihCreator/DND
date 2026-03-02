from enum import Enum, auto
from typing import Optional


class ViewFog(Enum):
    FULL = auto()
    DIFF = auto()


class BufferManager:
    def __init__(self):
        self._is_enabled = False
        self._active_contexts: set[str] = set()
        
        self._tokens: dict[tuple[str, str], tuple[tuple[float, float], float]] = {}
        self._fog: dict[str, list[tuple[ViewFog, bool, list]]] = {}
        self._images: dict[str, str] = {}
    
    @property
    def is_enabled(self) -> bool:
        return self._is_enabled
    
    def enable(self, state: bool = True):
        self._is_enabled = state
        if not state:
            self._active_contexts.clear()
    
    def mark_active(self, contextID: str):
        self._active_contexts.add(contextID)
    
    def should_buffer(self, contextID: Optional[str]) -> bool:
        if not self._is_enabled:
            return False
        if contextID is None:
            return True
        return contextID not in self._active_contexts
    
    def addToken(self, map_name: str, mime: str, pos: tuple[float, float], scale: float):
        self._tokens[(map_name, mime)] = (pos, scale)
    
    def removeToken(self, map_name: str, mime: str):
        if (map_name, mime) in self._tokens:
            del self._tokens[(map_name, mime)]
    
    def moveToken(self, map_name: str, mime: str, pos: tuple[float, float]):
        key = (map_name, mime)
        if key in self._tokens:
            _, current_scale = self._tokens[key]
            self._tokens[key] = (pos, current_scale)
    
    def popTokens(self, map_name: str):
        keys_to_remove = []
        
        for (m_name, mime), (pos, scale) in self._tokens.items():
            if m_name == map_name:
                yield mime, pos, scale
                keys_to_remove.append((m_name, mime))
        
        for k in keys_to_remove:
            del self._tokens[k]
        return
    
    def addFog(self, map_name: str, view: ViewFog, reveal: bool, data: list):
        self._fog.setdefault(map_name, [])
        if view == ViewFog.FULL:
            self._fog[map_name] = [(view, reveal, data)]
        else:
            self._fog[map_name].append((view, reveal, data))
    
    def popFog(self, map_name: str):
        return self._fog.pop(map_name, [])
    
    def addImage(self, name: str, path: str):
        self._images[name] = path
    
    def getImage(self, name: str) -> Optional[str]:
        return self._images.get(name)
    
    def popImage(self, name: str) -> Optional[str]:
        return self._images.pop(name, None)
    
    def getAllImages(self):
        return self._images.copy()
