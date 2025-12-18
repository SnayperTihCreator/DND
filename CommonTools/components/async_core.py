import uuid
from typing import Optional, Callable, Any
from loguru import logger

from attrs import define, field

from CommonTools.messages import BaseMessage, CommonActionType, RequestMessage


@define
class BaseContext:
    uid: str = field(factory=lambda: uuid.uuid4().hex, init=False)
    
    on_error: Optional[Callable] = field(default=None)
    on_done: Optional[Callable] = field(default=None)


@define
class ResourceContext(BaseContext):
    name: str = field(default="")
    namespace: str = field(default="")


class RequestContainer:
    
    def __init__(self):
        self._requests: dict[str, BaseContext] = {}
        self._namespaces: dict[str, dict[str, str]] = {}
    
    def addNameSpace(self, name: str):
        if name not in self._namespaces:
            self._namespaces[name] = {}
    
    def add(self, ctx: BaseContext):
        self._requests[ctx.uid] = ctx
        if not isinstance(ctx, ResourceContext):
            return
        ns = ctx.namespace
        if ns not in self._namespaces:
            self.addNameSpace(ns)
        self._namespaces[ns][ctx.name] = ctx.uid
    
    def get_by_uid(self, uid: str) -> Optional[BaseContext]:
        return self._requests.get(uid)
    
    def get_resource_uid(self, namespace: str, key: str) -> Optional[str]:
        return self._namespaces.setdefault(namespace, {}).get(key)
    
    def pop(self, uid: str) -> Optional[BaseContext]:
        ctx = self._requests.pop(uid, None)
        if ctx and isinstance(ctx, ResourceContext):
            ns_dict = self._namespaces.get(ctx.namespace)
            if ns_dict and ns_dict.get(ctx.name) == uid:
                ns_dict.pop(ctx.name)
        return ctx


class AsyncRequestManager:
    
    def __init__(self):
        self.storage = RequestContainer()
        self.storage.addNameSpace("images")
    
    def register(self, ctx: BaseContext):
        self.storage.add(ctx)
        return ctx.uid
    
    def handle_message(self, msg: RequestMessage | BaseMessage):
        if msg.type not in [CommonActionType.DONE_CALL, CommonActionType.ERROR_CALL, CommonActionType.IGNORE_CALL]:
            return False
        uid = msg.uid_callback
        ctx = self.storage.get_by_uid(uid)
        if ctx is None:
            return False
        
        match msg.type:
            case CommonActionType.DONE_CALL if isinstance(ctx, ResourceContext):
                return True
            case CommonActionType.DONE_CALL:
                if callable(ctx.on_done):
                    ctx.on_done(ctx, None)
                self.storage.pop(uid)
            case CommonActionType.IGNORE_CALL:
                self.storage.pop(uid)
            case CommonActionType.ERROR_CALL:
                if callable(ctx.on_error):
                    ctx.on_error(ctx)
                self.storage.pop(uid)
        return True
    
    def handle_resource(self, namespace: str, name: str, data: Any):
        uid = self.storage.get_resource_uid(namespace, name)
        if uid is None:
            return
        ctx = self.storage.get_by_uid(uid)
        if isinstance(ctx, ResourceContext):
            if callable(ctx.on_done):
                ctx.on_done(ctx, data)
            self.storage.pop(uid)
            