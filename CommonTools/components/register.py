from typing import Any, Optional
from attrs import define, field


@define(repr=False)
class Register:
    _data: dict[str, Any] = field(factory=dict, init=False, repr=False)
    
    def create(self, key: str, value: Any):
        self._data.setdefault(key, value)
    
    def get(self, name: str) -> Optional[Any]:
        return self._data.get(name, None)
    
    def __repr__(self):
        return f"Register({len(self._data)}"
