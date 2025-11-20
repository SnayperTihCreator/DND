from typing import ClassVar, Type, Any, Self
from enum import Enum

import json5
from pydantic import BaseModel


class SerializableMixin:
    """Миксин для автоматической сериализации/десериализации"""
    
    # Регистр всех сериализуемых классов
    _type_registry: ClassVar[dict[str, Type]] = {}
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        SerializableMixin._type_registry[cls.__qualname__] = cls
    
    def to_dict(self) -> dict[str, Any]:
        """Сериализация в словарь с тегом типа"""
        if isinstance(self, BaseModel):
            data = self.model_dump()
        else:
            data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        data['_type'] = self.__class__.__qualname__
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Десериализация из словаря по тегу типа"""
        type_name = data.get('_type')
        target_cls = cls._type_registry.get(type_name)
        if not target_cls:
            print(type_name, cls._type_registry)
            raise ValueError(f"Unknown type: {type_name}")
        
        # Удаляем тег перед созданием объекта
        data_without_tag = {k: v for k, v in data.items() if k != '_type'}
        
        if issubclass(target_cls, BaseModel):
            return target_cls.model_validate(data_without_tag)
        else:
            return target_cls(**data_without_tag)
    
    @classmethod
    def from_str(cls, data: str) -> Self:
        request = json5.loads(data)
        return cls.from_dict(request)


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


class BaseMessage(BaseModel, SerializableMixin):
    type: ClassVar[BaseActionType]
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.type = kwargs.get("type", NotActionType.NOT_TYPE)
