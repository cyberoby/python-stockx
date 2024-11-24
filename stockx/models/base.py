from __future__ import annotations

from collections.abc import Iterable
from dataclasses import (
    Field,
    dataclass, 
    field,
    fields,
)
from datetime import datetime
from inspect import get_annotations
from types import UnionType
from typing import ( 
    Any,
    get_args, 
    get_origin, 
)


@dataclass(frozen=True, slots=True)
class Response: 
    status_code: int
    message: str = '', 
    data: dict[str, Any] | list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StockXBaseModel:

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> StockXBaseModel:
        matching_kwargs = {
            key: val for key, val in _camel_to_snake(json).items() 
            if key in cls.__match_args__
        }
        
        annotations = cls.annotations()
        kwargs = {
            key: _convert(val, type_hint=annotations[key])
            for key, val in matching_kwargs.items()
        }      
        
        return cls(**kwargs)
    
    @classmethod
    def annotations(cls) -> dict[str, Any]:
        this_annotations = get_annotations(cls, eval_str=True)

        super_annotations = {}
        if len(cls.__mro__) > 1:
            super_cls = cls.__mro__[1]
            if hasattr(super_cls, 'annotations'):
                super_annotations = super_cls.annotations()

        return {**super_annotations, **this_annotations}

    
    def __str__(self, level: int = 0) -> str:
        indent = '  ' * level
        class_name = self.__class__.__name__

        def format(value, level):
            if isinstance(value, StockXBaseModel):
                return f'\n{value.__str__(level + 1)}'
            elif isinstance(value, Iterable) and not isinstance(value, str):
                return f''.join(format(item, level + 1) for item in value)
            return str(value)
        
        def value(field: Field):
            return getattr(self, field.name)

        attributes = '\n'.join(
            f'{indent}  {field.name}: {format(value(field), level + 1)}'
            for field in fields(self)
        )

        return f'{indent}{class_name}:\n{attributes}'


def _camel_to_snake(json: dict[str, Any]) -> dict[str, Any]:

    def snake(key: str) -> str:
        return ''.join(f'_{c.lower()}' if c.isupper() else c for c in key)
    
    return {snake(key): value for key, value in json.items()}


def _convert(value, type_hint):
    if value is None:
        return None
    
    if type_hint is datetime:
        return datetime.fromisoformat(value)
    
    elif get_origin(type_hint) is list:
        nested_type_hint = get_args(type_hint)[0]
        return [_convert(v, nested_type_hint) for v in value]
    
    elif get_origin(type_hint) is UnionType:
        optional_type, none_type = get_args(type_hint)
        if none_type is type(None):
            return _convert(value, optional_type)
        
    elif issubclass(type_hint, StockXBaseModel):
        return type_hint.from_json(value)
    
    else:
        return type_hint(value)