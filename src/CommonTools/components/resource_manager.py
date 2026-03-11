import inspect
import logging
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum, auto
from os import PathLike
from pathlib import Path
from typing import Any, Optional

from attrs import define

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    SUCCESS = auto()
    DROPPED = auto()
    ERROR = auto()


@define
class CallbackTask:
    callback: Any
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    
    @staticmethod
    def _make_week(obj):
        if inspect.ismethod(obj):
            return weakref.WeakMethod(obj)
        try:
            return weakref.ref(obj)
        except TypeError:
            return obj
    
    @staticmethod
    def _resolve_weak(obj):
        return obj() if isinstance(obj, weakref.ReferenceType) else obj
    
    @classmethod
    def create(cls, callback: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
        return cls(
            cls._make_week(callback),
            tuple(cls._make_week(arg) for arg in args),
            {k: cls._make_week(v) for k, v in kwargs.items()}
        )
    
    def execute(self, path: Optional[PathLike[str]]) -> TaskStatus:
        callback = self._resolve_weak(self.callback)
        if callback is None:
            return TaskStatus.DROPPED
        
        args = tuple(self._resolve_weak(arg) for arg in self.args)
        kwargs = {k: self._resolve_weak(v) for k, v in self.kwargs.items()}
        
        if any(a is None for a in args) or any(v is None for v in kwargs.values()):
            return TaskStatus.DROPPED
        
        try:
            callback(path, *args, **kwargs)
            return TaskStatus.SUCCESS
        except Exception as e:
            logger.error(f"Ошибка внутри коллбека: {e}")
            return TaskStatus.ERROR


class BaseResourceManager(ABC):
    def __init__(self, folder: str | PathLike[str]):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        
        self._tasks: dict[str, list[CallbackTask]] = defaultdict(list)
    
    def add_task(self, filename: str, callback: Any, args: tuple[Any, ...]=None, kwargs: dict[str, Any] = None):
        args = args or tuple()
        kwargs = kwargs or {}
        
        local_path = self.folder / filename
        if local_path.exists() and local_path.is_file():
            try:
                callback(local_path, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка при мгновенном вызове коллбека для {filename}: {e}")
            return
        
        task = CallbackTask.create(callback, args, kwargs)
        self._tasks[filename].append(task)
        
        self._on_file_missing(filename)
    
    @abstractmethod
    def _on_file_missing(self, filename: str):
        ...
    
    def resolve_file(self, filename: str, success: bool = True) -> TaskStatus:
        if filename not in self._tasks:
            return
        
        path = (self.folder / filename) if success else None
        tasks = self._tasks.pop(filename)
        
        for task in tasks:
            status = task.execute(path)
            
            if status == TaskStatus.DROPPED:
                logger.debug(f"Задача для {filename} отменена (целевые объекты были удалены).")
            elif status == TaskStatus.ERROR:
                logger.warning(f"Задача для {filename} завершилась с ошибкой.")
