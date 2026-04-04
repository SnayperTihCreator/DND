import importlib.metadata

try:
    __version__ = importlib.metadata.version("dnd")
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.1.0b2"
