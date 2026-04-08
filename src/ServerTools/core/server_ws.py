from typing import Protocol, Optional

from attrs import define, field
from websockets import Server, serve, ServerConnection


class ServerTableProtocol(Protocol):
    async def handle_websocket(self, websocket): ...


@define
class ServerWS:
    server: ServerTableProtocol
    runner: Optional[Server] = field(init=False, default=None)
    port: int = field(default=8765)
    
    async def start(self):
        for port in range(8765, 8780):
            try:
                self.runner = await serve(self._handle, "0.0.0.0", port)
                self.port = port
                return port
            except OSError:
                continue
        raise RuntimeError("No running server")
    
    async def stop(self):
        self.runner.close()
    
    async def _handle(self, websocket: ServerConnection):
        try:
            await self.server.handle_websocket(websocket)
        except Exception as e:
            pass