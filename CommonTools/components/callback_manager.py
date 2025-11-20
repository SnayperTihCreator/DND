from typing import Callable
import uuid

from CommonTools.messages import *


class CallbackManager:
    def __init__(self):
        self._callback_done: dict[str, Callable] = {}
        self._callback_error: dict[str, Callable] = {}
        self._callback_ignore: dict[str, Callable] = {}
    
    def handle(self, msg: BaseMessage):
        match msg.type:
            case CommonActionType.DONE_CALL:
                return self._handle_done_call(msg)
            case CommonActionType.ERROR_CALL:
                return self._handle_error_call(msg)
            case CommonActionType.IGNORE_CALL:
                return self._handle_ignore_call(msg)
        return False
    
    def register(self, done=None, error=None, ignore=None) -> str:
        uid = uuid.uuid4().hex
        self._callback_done[uid] = done
        self._callback_error[uid] = error
        self._callback_ignore[uid] = ignore
        return uid
    
    def _handle_done_call(self, msg: DoneCallback):
        if impl := self._callback_done.pop(msg.uid_callback, None):
            self._callback_ignore.pop(msg.uid_callback, None)
            self._callback_error.pop(msg.uid_callback, None)
            if callable(impl):
                impl()
            return True
    
    def _handle_error_call(self, msg: ErrorCallback):
        if impl := self._callback_error.pop(msg.uid_callback, None):
            self._callback_done.pop(msg.uid_callback, None)
            self._callback_ignore.pop(msg.uid_callback, None)
            if callable(impl):
                impl()
            return True
    
    def _handle_ignore_call(self, msg: IgnoreCallback):
        if impl := self._callback_ignore.pop(msg.uid_callback, None):
            self._callback_done.pop(msg.uid_callback, None)
            self._callback_error.pop(msg.uid_callback, None)
            if callable(impl):
                impl()
            return True
