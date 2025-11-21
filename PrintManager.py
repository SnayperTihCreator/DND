try:
    builtins = __import__("__builtin__")
except ImportError:
    builtins = __import__("builtins")
import sys
import inspect
from typing import Any, Callable, Optional, TextIO
import os


class PrintManager:
    def __init__(self) -> None:
        self._original_print = builtins.print
        self._enabled = False
        self._output_stream: TextIO = sys.stdout
        self._prefix: str = ""
        self._suffix: str = ""
        self._transform_func: Optional[Callable[[str], str]] = None
        self._show_caller_info = False
        self._caller_format = "[{file}:{line} in {function}] "

        builtins.print_manager = self

    def enable(self) -> None:
        """Включает кастомный print."""
        if not self._enabled:
            builtins.print = self._custom_print
            self._enabled = True

    def disable(self) -> None:
        """Отключает кастомный print, восстанавливает оригинальный."""
        if self._enabled:
            builtins.print = self._original_print
            self._enabled = False

    def set_output(self, stream: TextIO) -> None:
        """Устанавливает выходной поток."""
        self._output_stream = stream

    def set_prefix(self, prefix: str) -> None:
        """Устанавливает префикс для каждого вывода."""
        self._prefix = prefix

    def set_suffix(self, suffix: str) -> None:
        """Устанавливает суффикс для каждого вывода."""
        self._suffix = suffix

    def set_transform(self, transform_func: Optional[Callable[[str], str]]) -> None:
        """Устанавливает функцию для трансформации текста."""
        self._transform_func = transform_func

    def show_caller_info(
        self, enable: bool = True, format_str: Optional[str] = None
    ) -> None:
        """
        Включает/отключает вывод информации о месте вызова.
        format_str может содержать {file}, {line}, {function} плейсхолдеры.
        """
        self._show_caller_info = enable
        if format_str:
            self._caller_format = format_str

    def _get_caller_info(self) -> str:
        """Возвращает информацию о вызывающей функции в заданном формате."""

        frame = inspect.currentframe()
        try:
            # Поднимаемся на 3 фрейма вверх:
            # 1. _get_caller_info
            # 2. _custom_print
            # 3. код, который вызвал print
            for _ in range(6):
                if frame is None:
                    continue
                if frame.f_code.co_name in ["_custom_print", "_get_caller_info"]:
                    frame = frame.f_back
            line = frame.f_lineno
            file = frame.f_code.co_filename
            function = frame.f_code.co_name

            return self._caller_format.format(
                file=os.path.basename(file),  # берем только имя файла
                line=line,
                function=function,
            )
        except AttributeError:
            return "[caller info unavailable] "
        finally:
            del frame  # важно для избежания циклов ссылок

    def _custom_print(self, *args: Any, **kwargs: Any) -> None:
        """Кастомная реализация print с поддержкой caller info."""
        if not self._enabled:
            return self._original_print(*args, **kwargs)

        text = " ".join(str(arg) for arg in args)

        if self._transform_func:
            text = self._transform_func(text)

        # Добавляем информацию о месте вызова если включено
        if self._show_caller_info:
            caller_info = self._get_caller_info()
        else:
            caller_info = ""

        full_text = f"{caller_info}{self._prefix}{text}{self._suffix}"

        print_args = {
            "file": kwargs.get("file", None) or self._output_stream,
            "end": kwargs.get("end", "\n"),
            "sep": kwargs.get("sep", " "),
            "flush": kwargs.get("flush", False),
        }
        self._original_print(full_text, **print_args)

    def __enter__(self) -> "PrintManager":
        """Поддержка контекстного менеджера."""
        self.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Восстанавливает оригинальный print при выходе из контекста."""
        self.disable()
