from typing import Optional

from attrs import define


@define
class NetworkConfig:
    ip: Optional[str] = None
    ws_port: Optional[int] = None
    http_port: Optional[int] = None
    
    @property
    def is_valid(self):
        return (self.ip is not None) and (self.ws_port is not None)
    
    def http(self, extra=""):
        return f"http://{self.ip}:{self.http_port}{extra}"
    
    def ws(self, extra=""):
        return f"ws://{self.ip}:{self.ws_port}{extra}"