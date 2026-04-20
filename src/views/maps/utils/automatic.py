from typing import TypeVar, Any

T = TypeVar("T")


def properties(name: str) -> property:
    def getter(self: Any) -> T:
        return self.property(name)
    
    def setter(self: Any, value: T) -> None:
        self.setProperty(name, value)
    
    return property(getter, setter)
