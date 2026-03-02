from typing import ClassVar, Type, Any, Self, Optional
from enum import Enum

import json5
from pydantic import BaseModel


class BaseActionType(Enum):
    """Базовый класс для всех типов действий"""
    
    def __init__(self, group: str, action: str, type_: str):
        self.group = group
        self.action = action
        self.type = type_
    
    def __str__(self) -> str:
        return f"{self.group}:{self.action}:{self.type}"
    
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
    
    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        data['_type'] = self.__class__.__qualname__
        return data
    
    def to_str(self) -> str:
        return json5.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        type_name = data.get('_type')
        target_cls: Optional[BaseMessage] = cls._registry.get(type_name)
        if not target_cls:
            print(type_name, cls._registry)
            raise ValueError(f"Unknown type: {type_name}")
        
        del data['_type']
        return target_cls.model_validate(data)
    
    @classmethod
    def from_str(cls, data: str) -> Self:
        request = json5.loads(data)
        return cls.from_dict(request)
    
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
