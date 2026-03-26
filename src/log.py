import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from contextvars import ContextVar

from PySide6.QtCore import QtMsgType, qInstallMessageHandler, QMessageLogContext

LOG_DIR = Path("./assets/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

ctx_role = ContextVar("role", default="APP")


class RoleInjectFilter(logging.Filter):
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "role"):
            record.role = ctx_role.get()
        return True


class LessThanFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.max_level = level
    
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def setup_logging(role="launcher"):
    ctx_role.set(role.upper())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    role_inject_filter = RoleInjectFilter()
    
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    
    formatter = logging.Formatter(
        "%(asctime)s: [%(role)s/%(name)s/%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    
    app_handler = TimedRotatingFileHandler(
        LOG_DIR / f"app_{role}.log",
        when="midnight",
        interval=1,
        encoding="utf-8",
        backupCount=5,
        delay=True,
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(role_inject_filter)
    app_handler.addFilter(LessThanFilter(logging.ERROR))
    
    error_handler = TimedRotatingFileHandler(
        LOG_DIR / "error.log",
        when="midnight",
        interval=1,
        encoding="utf-8",
        backupCount=1,
        delay=True,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(role_inject_filter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(role_inject_filter)
    
    logging.basicConfig(handlers=[app_handler, error_handler, console_handler])
    
    qInstallMessageHandler(qt_message_handler)
    sys.excepthook = exception_handler
    
    logging.info("Logging system initialized.")


def qt_message_handler(mode: QtMsgType, context: QMessageLogContext, message):
    level = logging.DEBUG
    match mode:
        case QtMsgType.QtInfoMsg:
            level = logging.INFO
        case QtMsgType.QtWarningMsg:
            level = logging.WARNING
        case QtMsgType.QtCriticalMsg:
            level = logging.ERROR
        case QtMsgType.QtFatalMsg:
            level = logging.CRITICAL
    category = context.category if context.category else "Qt"
    
    logger = logging.getLogger(f"Qt.{category}")
    logger.log(level, message)


def exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    root_logger = logging.getLogger()
    root_logger.critical("Uncaught exception (Global Crash):", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


setup_logging()
