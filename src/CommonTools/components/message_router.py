import logging
import weakref
import asyncio
import inspect

logger = logging.getLogger(__name__)


class RouterDescriptor:
    def __init__(self):
        self._handlers = {}
        self.bound_dispatchers = weakref.WeakKeyDictionary()
    
    def handler(self, msg_type):
        def decorator(func):
            self._handlers.setdefault(msg_type, []).append(func)
            return func
        
        return decorator
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        if instance in self.bound_dispatchers:
            return self.bound_dispatchers[instance]
        
        async def bound_dispatch(uid, msg):
            return await self.dispatch(instance, uid, msg)
        
        self.bound_dispatchers[instance] = bound_dispatch
        return bound_dispatch
    
    async def dispatch(self, instance, uid, msg):
        if not (handlers := self._handlers.get(msg.type)):
            return False
        
        result = []
        for handler_func in handlers:
            if inspect.iscoroutinefunction(handler_func):
                result.append(await handler_func(instance, uid, msg))
            else:
                result.append(handler_func(instance, uid, msg))
            await asyncio.sleep(0)
        
        return any(result)
