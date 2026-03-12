import base64
import binascii
from pathlib import Path
from typing import ClassVar, Type, Optional, Self, Any
from pydantic import BaseModel, ValidationError, model_serializer, model_validator
from pydantic_core.core_schema import SerializerFunctionWrapHandler

NESTING_SEPARATOR = '>>'


class BaseMime(BaseModel):
    _registry: ClassVar[dict[str, Type["BaseMime"]]] = {}
    _prefix: ClassVar[str]
    _extension: ClassVar[str]
    
    nested_mime: Optional[Self] = None
    
    def __init_subclass__(cls, *, prefix: str, extension: str = "", **kwargs):
        super().__init_subclass__()
        cls._prefix = prefix
        cls._extension = extension
        BaseMime._registry[prefix] = cls
    
    @model_serializer(mode="wrap")
    def _serializer_with_prefix(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        data["_prefix"] = self._prefix
        return data
    
    @model_validator(mode="wrap")
    @classmethod
    def _smart_parser(cls, data: Any, handler: Any) -> Any:
        if isinstance(data, BaseMime):
            return data
        
        if isinstance(data, dict):
            prefix = data.get("_prefix")
            if prefix:
                target = cls._registry.get(prefix)
                if not target:
                    raise ValueError(f"Неизвестный MIME-префикс: {prefix}")
                
                if cls is target:
                    data2 = data.copy()
                    data2.pop("_prefix", None)
                    return handler(data2)
                
                data2 = data.copy()
                data2.pop("_prefix", None)
                return target.model_validate(data2)
        
        return handler(data)
    
    def hasExtension(self) -> bool:
        return bool(self._extension)
    
    def to_str(self) -> str:
        """Собирает MIME-строку, включая вложенную часть."""
        parts = [self._prefix]
        dumped = self.model_dump(exclude={'nested_mime'}, exclude_defaults=True, mode="json")
        dumped.pop("_prefix", None)
        parts.extend(str(v) for v in dumped.values())
        base_str = ":".join(parts)
        
        if self.nested_mime:
            return f"{base_str}{NESTING_SEPARATOR}{self.nested_mime.to_str()}"
        return base_str
    
    @classmethod
    def from_str(cls, mime_str: str) -> Optional["BaseMime"]:
        """Двухступенчатый парсер: сначала отделяет вложенность по '>>'."""
        if NESTING_SEPARATOR in mime_str:
            parent_part, nested_part = mime_str.split(NESTING_SEPARATOR, 1)
            
            parent_obj = cls._parse_single(parent_part)
            nested_obj = cls.from_str(nested_part)
            
            if parent_obj and nested_obj:
                parent_obj.nested_mime = nested_obj
                return parent_obj
            return None
        
        else:
            return cls._parse_single(mime_part=mime_str)
    
    @classmethod
    def _parse_single(cls, mime_part: str) -> Optional["BaseMime"]:
        sorted_prefixes = sorted(cls._registry.items(), key=lambda x: len(x[0]), reverse=True)
        
        for prefix, model_cls in sorted_prefixes:
            if mime_part.startswith(prefix + ':'):
                data_part = mime_part.removeprefix(prefix + ':')
                data_values = data_part.split(":")
                
                field_names = [f for f in model_cls.model_fields if f != 'nested_mime']
                
                if len(data_values) > len(field_names):
                    continue
                
                try:
                    data_dict = dict(zip(field_names, data_values))
                    return model_cls(**data_dict)
                except ValidationError:
                    continue
        return None
    
    @staticmethod
    def mime_to_filename(mime: str, extension: str) -> str:
        """Кодирует MIME в безопасное для файловой системы имя с помощью base64."""
        mime_bytes = mime.encode('utf-8')
        b64_bytes = base64.urlsafe_b64encode(mime_bytes)
        b64_string = b64_bytes.decode('utf-8').rstrip('=')
        return f"{b64_string}{extension}"
    
    def to_file(self, extension=None):
        ext = extension or self._extension
        return self.mime_to_filename(self.to_str(), ext)
    
    @staticmethod
    def filename_to_mime(filename: str) -> str | None:
        """Декодирует имя файла обратно в MIME-строку."""
        b64_string = Path(filename).stem
        padding = '=' * (4 - len(b64_string) % 4)
        b64_string_padded = b64_string + padding
        try:
            b64_bytes = b64_string_padded.encode('utf-8')
            mime_bytes = base64.urlsafe_b64decode(b64_bytes)
            return mime_bytes.decode('utf-8')
        except (TypeError, ValueError, binascii.Error):
            return None
    
    @classmethod
    def from_file(cls, filename: str) -> Optional[Self]:
        mime = cls.filename_to_mime(filename)
        if not mime: return None
        return cls.from_str(mime)
