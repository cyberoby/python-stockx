from __future__ import annotations

from dataclasses import dataclass, field, fields
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

    
    # def __str__(self) -> str:
        #string_args = (
        #    f'    {field.name}={str(getattr(self, field.name))}' 
        #    for field in fields(self)
        #)
        #return f'{self.__class__.__name__}(\n{'\n'.join(string_args)}\n)'


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