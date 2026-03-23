from pathlib import Path
from typing import Annotated, Any, Tuple

from PySide6.QtCore import QPoint, QPointF, QSize
from PySide6.QtGui import QColor
from pydantic import BeforeValidator, PlainSerializer


# --- Вспомогательные функции ---

def _to_point(v: Any) -> QPoint:
    if isinstance(v, QPoint): return v
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return QPoint(int(v[0]), int(v[1]))
    raise ValueError(f"Cannot convert {v} to QPoint")


def _to_size(v: Any) -> QSize:
    if isinstance(v, QSize): return v
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return QSize(int(v[0]), int(v[1]))
    raise ValueError(f"Cannot convert {v} to QSize")


def _to_color(v: Any) -> QColor:
    if isinstance(v, QColor): return v
    if isinstance(v, str): return QColor(v)  # Поддержка "#RRGGBB" или "red"
    if isinstance(v, (list, tuple)) and len(v) in (3, 4):
        return QColor(*v)
    raise ValueError(f"Cannot convert {v} to QColor")


def _to_path(v: Any) -> Path:
    if isinstance(v, Path):
        return v
    return Path(str(v))


def _serialize_path(v: Path) -> str:
    return v.as_posix()


# --- Аннотированные типы для Pydantic ---

QtPoint = Annotated[
    QPoint,
    BeforeValidator(_to_point),
    PlainSerializer(lambda v: (v.x(), v.y()), return_type=Tuple[int, int])
]

QtSize = Annotated[
    QSize,
    BeforeValidator(_to_size),
    PlainSerializer(lambda v: (v.width(), v.height()), return_type=Tuple[int, int])
]

QtColor = Annotated[
    QColor,
    BeforeValidator(_to_color),
    PlainSerializer(lambda v: v.name(), return_type=str)  # Сериализуем в HEX-строку
]

# Аналоги для Float версий (F)
QtPointF = Annotated[
    QPointF,
    BeforeValidator(lambda v: QPointF(v[0], v[1]) if isinstance(v, (list, tuple)) else v),
    PlainSerializer(lambda v: (v.x(), v.y()), return_type=Tuple[float, float])
]

QtPath = Annotated[
    Path,
    BeforeValidator(_to_path),
    PlainSerializer(_serialize_path, return_type=str)
]
