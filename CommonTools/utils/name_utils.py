import re

from PySide6.QtCore import QPointF

"""
MIME format:
'token-type @ x, y, scale : args1 | args2 | argsn...'
"""

MIME_TOKEN_FORMAT = re.compile(r"^(\w+)\s*@"
                               r"\s*(?:([-\d.]+)\s*,\s*([-\d.]+)\s*,"
                               r"\s*([-\d.]+)|request\s*)"
                               r"(?:\s*:\s*(.*))?$")

FORBIDDEN_CHARS = re.compile(r"[|:@\n\r\t\"'`\\<>,]")


def fromPointScale(ttype: str, pos: QPointF, scale: float, *args) -> str:
    return f"{ttype}@{pos.x()},{pos.y()},{scale}:" + "|".join(args)


def fromTupleScale(ttype: str, pos: tuple, scale: float, *args) -> str:
    return f"{ttype}@{pos[0]},{pos[1]},{scale}:" + "|".join(args)
