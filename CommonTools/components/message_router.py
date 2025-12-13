from PySide6.QtCore import QCoreApplication


class MessageRouter:
    def __init__(self):
        self._handlers = {}
    
    def handler(self, msg_type):
        """Декоратор для регистрации обработчика."""
        
        def decorator(func):
            self._handlers.setdefault(msg_type, []).append(func)
            return func
        
        return decorator
    
    def dispatch(self, obj, uid, msg):
        if not (handlers := self._handlers.get(msg.type)):
            return False
        for handler in handlers:
            handler(obj, uid, msg)  # obj — это self экземпляра
            QCoreApplication.processEvents()
        return True
