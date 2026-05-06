from typing import ClassVar, Type, Any, Self, Optional
from enum import Enum

import json5
from pydantic import BaseModel, model_serializer, model_validator, SecretStr
from pydantic_core.core_schema import SerializerFunctionWrapHandler


class BaseActionType(Enum):
    """Базовый класс для всех типов действий"""
    
    def __init__(self, group: str, action: str, type_: str):
        self.group = group
        self.action = action
        self.type = type_
    
    def __str__(self) -> str:
        return f"{self.group}:{self.action}:{self.type}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}({self!s})>"
    
    @classmethod
    def get_by_group(cls, group: str) -> list:
        """Получить все действия определенной группы"""
        return [item for item in cls if item.group == group]
    
    @classmethod
    def get_by_group_action(cls, group: str, action: str) -> list:
        """Получить действия по группе и действию"""
        return [item for item in cls if item.group == group and item.action == action]
    
    @classmethod
    def validate_group_action(cls, group: str, action: str, type_: str) -> bool:
        """Проверить существование комбинации группа:действие:вид"""
        return any(
            item.group == group and item.action == action and item.type == type_
            for item in cls
        )


class NotActionType(BaseActionType):
    NOT_TYPE = ("service", "action", "not")


class BaseMessage(BaseModel):
    type: ClassVar[BaseActionType]
    _registry: ClassVar[dict[str, Type["BaseMessage"]]] = {}
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        cls.type = kwargs.get("type", NotActionType.NOT_TYPE)
        cls._registry[cls.__qualname__] = cls
    
    @model_serializer(mode="wrap")
    def _serializer_with_type(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)
        data["_type"] = self.__class__.__qualname__
        return data
    
    @model_validator(mode="wrap")
    @classmethod
    def _smart_parser(cls, data: Any, handler: Any) -> Any:
        if isinstance(data, BaseMessage):
            return data
        
        if isinstance(data, str):
            data = json5.loads(data)
        
        if isinstance(data, dict):
            target_name = data.get("_type")
            if target_name:
                target = cls._registry.get(target_name)
                
                if not target:
                    raise ValueError(f"Unknown message type: {target_name}")
                
                if cls is target:
                    data2 = data.copy()
                    data2.pop("_type", None)
                    return handler(data2)
                
                data2 = data.copy()
                data2.pop("_type", None)
                return target.model_validate(data2)
        
        return handler(data)
    
    def to_dict(self, secure: bool = False) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        if not secure:
            for field_name, field_info in self.model_fields.items():
                extra = field_info.json_schema_extra
                if extra and extra.get("is_socket"):
                    value = getattr(self, field_name)
                    if isinstance(value, SecretStr):
                        data[field_name] = value.get_secret_value()
        data["_type"] = self.__class__.__qualname__
        return data
    
    def to_str(self) -> str:
        return json5.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)
    
    @classmethod
    def from_str(cls, data: str) -> Self:
        return cls.model_validate(data)
    
    @classmethod
    def get_type_msg(cls, data: dict[str, Any]) -> Optional[BaseActionType]:
        if not (cls_name := data.get("_type")):
            return None
        target_cls: Optional[BaseMessage] = cls._registry.get(cls_name)
        if target_cls:
            return target_cls.type
        return None


class BaseSystemMessage(BaseMessage):
    pass


def get_type_msg(data: dict[str, Any]) -> Optional[BaseActionType]:
    return BaseMessage.get_type_msg(data)
