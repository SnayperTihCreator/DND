import importlib.metadata
import logging

logger = logging.getLogger(__name__)

try:
    __version__ = importlib.metadata.version("dnd")
except importlib.metadata.PackageNotFoundError:
    logger.warning("Could not find DND package")
    __version__ = "1.1.0b2"
