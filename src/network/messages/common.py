from .core import BaseActionType, BaseMessage


class CommonActionType(BaseActionType):
    ERROR = ("common", "error", "data")
    DONE_CALL = ("common", "done", "callback")
    ERROR_CALL = ("common", "error", "callback")
    IGNORE_CALL = ("common", "ignore", "callback")


class ErrorMessage(BaseMessage, type=CommonActionType.ERROR):
    error: str


class RequestMessage(BaseMessage):
    uid_callback: str


class DoneCallback(RequestMessage, type=CommonActionType.DONE_CALL):
    pass


class ErrorCallback(RequestMessage, type=CommonActionType.ERROR_CALL):
    error: str


class IgnoreCallback(RequestMessage, type=CommonActionType.IGNORE_CALL):
    pass


__all__ = [
    "CommonActionType", "RequestMessage",
    "ErrorMessage", "ErrorCallback",
    "IgnoreCallback", "DoneCallback"
]
