from typing import ClassVar, Type, Optional, Self

from pydantic import BaseModel, ValidationError


class BaseMime(BaseModel):
    _registry: ClassVar[dict[str, Type["BaseMime"]]] = {}
    _prefix: ClassVar[str] = ""
    
    def __init_subclass__(cls, **kwargs):
        cls._prefix = kwargs.get("prefix", "not-prefixed")
        if cls._prefix != "not-prefixed":
            cls._registry[cls._prefix] = cls
    
    def to_str(self) -> str:
        parts = [self._prefix]
        parts.extend(str(v) for v in self.model_dump().values())
        return ":".join(parts)
    
    @classmethod
    def from_str(cls, mime: str) -> Optional[Self]:
        for prefix, model_cls in cls._registry.items():
            if mime.startswith(prefix + ':'):
                data_part = mime.removeprefix(prefix + ':')
                data_values = data_part.split(":")
                
                field_names = list(model_cls.model_fields.keys())
                if len(field_names) != len(data_values):
                    continue
                
                try:
                    data = dict(zip(field_names, data_values))
                    return model_cls.model_validate(data)
                except ValidationError:
                    continue
        return None
