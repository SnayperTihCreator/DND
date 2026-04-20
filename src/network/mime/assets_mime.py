from pydantic import Field

from .core import BaseMime


class AssetsMime(BaseMime, prefix="assets"):
    category: str
    filename: str = Field("")


__all__ = [
    "AssetsMime",
]
