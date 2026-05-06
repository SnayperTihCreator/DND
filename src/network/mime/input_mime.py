from .core import BaseMime


class InputMime(BaseMime, prefix="request"):
    category: str


__all__ = ["InputMime"]