import re
from typing import ClassVar, Type, Optional, Self, Any

from pydantic import BaseModel, ValidationError, model_serializer, model_validator
from pydantic_core.core_schema import SerializerFunctionWrapHandler


class BaseMime(BaseModel):
    _registry: ClassVar[dict[str, Type["BaseMime"]]] = {}
    _prefix: ClassVar[str]
    
    _TOKENIZER_RE: ClassVar[re.Pattern] = re.compile(r'([<>:])')
    
    def __init_subclass__(cls, *, prefix: str, **kwargs):
        super().__init_subclass__()
        cls._prefix = prefix
        BaseMime._registry[prefix] = cls
    
    @model_serializer(mode="wrap")
    def _serializer_with_prefix(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        data["_prefix"] = self._prefix
        return data
    
    @model_validator(mode="wrap")
    @classmethod
    def _smart_parser(cls, data: Any, handler: Any) -> Any:
        if isinstance(data, str) and data.startswith("<") and data.endswith(">"):
            inner_str = data[1:-1]
            parsed_inner = BaseMime.from_str(inner_str)
            if parsed_inner:
                return parsed_inner
            raise ValueError(f"Ошибка парсинга вложенного MIME: {inner_str}")
        
        if isinstance(data, BaseMime):
            return data
        
        if isinstance(data, dict):
            prefix = data.get("_prefix")
            if prefix:
                target = cls._registry.get(prefix)
                if not target:
                    raise ValueError(f"Неизвестный MIME-префикс: {prefix}")
                
                data2 = data.copy()
                data2.pop("_prefix", None)
                if cls is target:
                    return handler(data2)
                return target.model_validate(data2)
        
        return handler(data)
    
    def to_str(self) -> str:
        """Собирает MIME-строку, оборачивая вложенные поля-MIME в скобки < >."""
        parts = [self._prefix]
        
        for name, field in self.model_fields.items():
            val = getattr(self, name)
            if val is None:
                continue
            
            if isinstance(val, BaseMime):
                parts.append(f"<{val.to_str()}>")
            else:
                parts.append(str(val))
        
        return ":".join(parts)
    
    @classmethod
    def from_str(cls, mime_str: str) -> Optional[Self]:
        """Разбивает строку на токены с учетом глубины скобок < > и парсит объект."""
        sorted_prefixes = sorted(cls._registry.items(), key=lambda x: len(x[0]), reverse=True)
        
        for prefix, model_cls in sorted_prefixes:
            if mime_str.startswith(prefix + ':'):
                data_part = mime_str.removeprefix(prefix + ':')
                
                tokens = cls._TOKENIZER_RE.split(data_part)
                data_values = []
                current_val = []
                depth = 0
                
                for token in tokens:
                    if not token:
                        continue
                    
                    if token == '<':
                        depth += 1
                        current_val.append(token)
                    elif token == '>':
                        depth -= 1
                        current_val.append(token)
                    elif token == ':' and depth == 0:
                        data_values.append("".join(current_val))
                        current_val.clear()
                    else:
                        current_val.append(token)
                
                if current_val:
                    data_values.append("".join(current_val))
                
                field_names = list(model_cls.model_fields.keys())
                
                if len(data_values) > len(field_names):
                    continue
                
                try:
                    data_dict = dict(zip(field_names, data_values))
                    return model_cls.model_validate(data_dict)
                except ValidationError:
                    continue
        return None
