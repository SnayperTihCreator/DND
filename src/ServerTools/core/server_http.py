from pathlib import Path
from typing import Protocol, Optional

import aiofiles
from attrs import field, define
from aiohttp import web
from psygnal import Signal

from CommonTools.core import ClientData, NetworkConfig
from .proxy import MasterProxyHandler


class ServerTableProtocol(Protocol):
    clients: dict[str, ClientData]
    proxy_handler: MasterProxyHandler
    assets: Path
    config: NetworkConfig
    
    file_loaded: Signal


@define
class ServerHttp:
    server: ServerTableProtocol
    runner: Optional[web.AppRunner] = field(default=None, init=False)
    port: int = field(default=8080)
    
    async def start(self):
        app = web.Application()
        app.router.add_get("/static/{filename}", self._handle_download)
        app.router.add_post('/upload', self._handle_upload)
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        
        for port in range(8080, 8100):
            try:
                site = web.TCPSite(self.runner, "0.0.0.0", port)
                await site.start()
                self.port = port
                return port
            except OSError:
                continue
        
        raise RuntimeError("No running server")
    
    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
    
    async def _handle_download(self, request: web.Request):
        uid = request.query.get("uid") or request.headers.get("X-User-ID")
        if not uid:
            return web.json_response({"error": "Missing UID"}, status=401)
        
        cd = self.server.clients.get(uid) or self.server.proxy_handler.uid
        if not cd or not cd.is_playing:
            return web.json_response({"error": "Forbidden: You are not an active player"}, status=403)
        
        filename = request.match_info.get("filename")
        if not filename:
            return web.json_response({"error": "Missing filename"}, status=400)
        
        filename = Path(filename).name
        path = self.server.assets / filename
        
        if not path.exists() or not path.is_file():
            return web.json_response({"error": "File not found"}, status=404)
        
        return web.FileResponse(path)
    
    async def _handle_upload(self, request: web.Request):
        uid = request.query.get("uid") or request.headers.get("X-User-ID")
        if not uid:
            return web.json_response({"error": "Missing UID"}, status=401)
        
        cd = self.server.clients.get(uid) or self.server.proxy_handler.uid
        if not cd or not cd.is_playing:
            return web.json_response({"error": "Forbidden: You are not an active player"}, status=403)
        
        reader = await request.multipart()
        field = await reader.next()
        
        filename = Path(field.filename).name
        path = self.server.assets / filename
        
        async with aiofiles.open(path, 'wb') as file:
            while True:
                chunk = await field.read_chunk()
                if not chunk: break
                await file.write(chunk)
        
        self.server.file_loaded.emit(field.filename)
        return web.json_response({'url': filename})
