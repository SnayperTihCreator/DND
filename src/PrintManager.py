import sys
import inspect
import os
import builtins
import logging
from typing import Any, Callable, Optional, TextIO

logger = logging.getLogger(__name__)


class PrintManager:
    def __init__(self) -> None:
        self._original_print = builtins.print
        self._enabled = False
        self._mute_console = False
        
        self._output_stream: TextIO = sys.stdout
        self._prefix: str = ""
        self._suffix: str = ""
        self._transform_func: Optional[Callable[[str], str]] = None
        
        self._show_caller_info = False
        self._caller_format = "[{file}:{line} in {function}] "
        
        builtins.print_manager = self
    
    def enable(self) -> None:
        """
        Enables interception. Prints go to log file (and console).
        """
        if not self._enabled:
            builtins.print = self._custom_print
            self._enabled = True
            logger.info("PrintManager enabled.")
    
    def disable(self) -> None:
        """
        Restores original print.
        """
        if self._enabled:
            builtins.print = self._original_print
            self._enabled = False
            logger.info("PrintManager disabled.")
    
    def mute(self) -> None:
        """
        Stop printing to console (Terminal), but KEEP logging to file.
        """
        self._mute_console = True
    
    def unmute(self) -> None:
        """
        Resume printing to console.
        """
        self._mute_console = False
    
    def set_output(self, stream: TextIO) -> None:
        self._output_stream = stream
    
    def set_prefix(self, prefix: str) -> None:
        self._prefix = prefix
    
    def set_suffix(self, suffix: str) -> None:
        self._suffix = suffix
    
    def set_transform(self, transform_func: Optional[Callable[[str], str]]) -> None:
        self._transform_func = transform_func
    
    def show_caller_info(self, enable: bool = True, format_str: Optional[str] = None) -> None:
        self._show_caller_info = enable
        if format_str:
            self._caller_format = format_str
    
    def _get_caller_info(self) -> str:
        frame = inspect.currentframe()
        try:
            while frame:
                code_name = frame.f_code.co_name
                if code_name not in ["_custom_print", "_get_caller_info", "enable"]:
                    break
                frame = frame.f_back
            
            if frame is None:
                return "[unknown] "
            
            line = frame.f_lineno
            file = frame.f_code.co_filename
            function = frame.f_code.co_name
            
            return self._caller_format.format(
                file=os.path.basename(file),
                line=line,
                function=function,
            )
        except Exception:
            return ""
        finally:
            del frame
    
    def _custom_print(self, *args: Any, **kwargs: Any):
        """
        The magic function: Logs everything, prints only if not muted.
        """
        if not self._enabled:
            return self._original_print(*args, **kwargs)
        
        # Prepare text
        text = " ".join(str(arg) for arg in args)
        
        if self._transform_func:
            text = self._transform_func(text)
        
        caller_info = ""
        if self._show_caller_info:
            caller_info = self._get_caller_info()
        
        full_text = f"{caller_info}{self._prefix}{text}{self._suffix}"
        
        logger.info(f"PRINT: {full_text}")
        
        if not self._mute_console:
            print_args = {
                "file": kwargs.get("file", None) or self._output_stream,
                "end": kwargs.get("end", "\n"),
                "sep": kwargs.get("sep", " "),
                "flush": kwargs.get("flush", False),
            }
            self._original_print(full_text, **print_args)
        return None
    
    def __enter__(self) -> "PrintManager":
        self.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disable()
