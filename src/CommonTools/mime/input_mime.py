from .core import BaseMime


class InputMime(BaseMime, prefix="request"):
    name: str


__all__ = ["InputMime"]