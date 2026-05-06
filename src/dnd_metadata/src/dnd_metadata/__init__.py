import importlib.metadata
import logging

logger = logging.getLogger(__name__)

version = importlib.metadata.version("dnd-metadata")
REPO = "SnayperTihCreator/DND"

__all__ = ["version", "REPO"]
