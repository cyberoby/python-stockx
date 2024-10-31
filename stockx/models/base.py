from __future__ import annotations

from dataclasses import dataclass, field
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

        annotations = get_annotations(cls, eval_str=True)
        kwargs = {
            key: _convert(val, type_hint=annotations[key])
            for key, val in matching_kwargs.items()
        }

        return cls(**kwargs)


def _camel_to_snake(json: dict[str, Any]) -> dict[str, Any]:

    def snake(key: str) -> str:
        return ''.join(f'_{c.lower()}' if c.isupper() else c for c in key)
    
    return {snake(key): value for key, value in json.items()}


def _convert(value, type_hint):
    if not value:
        return None
    
    if type_hint is datetime:
        return datetime.fromisoformat(value)
    
    elif get_origin(type_hint) is list:
        nested_type_hint, _ = get_args(type_hint)
        return [_convert(v, nested_type_hint) for v in value]
    
    elif get_origin(type_hint) is UnionType:
        optional_type, none_type = get_args(type_hint)
        if none_type is type(None):
            return _convert(value, optional_type)
        
    elif issubclass(type_hint, StockXBaseModel):
        return type_hint.from_json(value)
    
    else:
        return type_hint(value)