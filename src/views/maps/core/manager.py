from __future__ import annotations

from typing import TYPE_CHECKING

from psygnal import Signal

from network.mime import TokenMime

if TYPE_CHECKING:
    from .map import Map


class Manager:
    token_added = Signal(TokenMime)
    token_moved = Signal()
    
    def __init__(self, scene: Map):
        self.map = scene
    
    def update_size_tokens(self):
        pass
