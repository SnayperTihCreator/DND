from .core import BaseActionType, BaseMessage


class CommonActionType(BaseActionType):
    ERROR = ("common", "error", "data")
    DONE_CALL = ("common", "done", "callback")
    ERROR_CALL = ("common", "error", "callback")
    IGNORE_CALL = ("common", "ignore", "callback")


class ErrorMessage(BaseMessage, type=CommonActionType.ERROR):
    error: str


class DoneCallback(BaseMessage, type=CommonActionType.DONE_CALL):
    uid_callback: str


class ErrorCallback(BaseMessage, type=CommonActionType.ERROR_CALL):
    uid_callback: str
    error: str


class IgnoreCallback(BaseMessage, type=CommonActionType.IGNORE_CALL):
    uid_callback: str


__all__ = [
    "CommonActionType",
    "ErrorMessage", "ErrorCallback",
    "IgnoreCallback", "DoneCallback"
]
