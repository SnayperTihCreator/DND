class ImageManager:
    def __init__(self):
        self._callbacks = {}
        
    def register(self, name, callback):
        self._callbacks[name] = callback
        
    def unregister(self, name):
        self._callbacks.pop(name, None)
        
    def handle(self, name, file_path):
        if impl := self._callbacks.pop(name, None):
            impl(name, file_path)