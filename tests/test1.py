from network.messages import *

msg = ClientStartPlayer(name="oleg", cls="oleg")

proxy = ProxyTunnel(uid="ff", msg=msg)

proxy2: ProxyTunnel = BaseMessage.from_str(proxy.to_str())

print(repr(proxy2.msg.type))