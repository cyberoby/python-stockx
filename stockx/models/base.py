from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from inspect import get_annotations
from types import UnionType
from typing import Any, get_args, get_origin

from ..format import pretty_str


@pretty_str
@dataclass(frozen=True, slots=True)
class StockXBaseModel:
    """Base class for all StockX models."""
    
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> StockXBaseModel:
        """Create a new instance from a JSON."""
        # Get the kwargs present in the json and the class
        matching_kwargs = {
            key: val for key, val in _camel_to_snake(json).items() 
            if key in cls.__match_args__
        }

        annotations = cls.annotations()

        # Convert the values to the hinted type
        kwargs = {
            key: _convert(val, type_hint=annotations[key])
            for key, val in matching_kwargs.items()
        }      
        
        return cls(**kwargs)
    
    @classmethod
    def annotations(cls) -> dict[str, Any]:
        """Get the annotations for the class and all superclasses."""
        this_annotations = get_annotations(cls, eval_str=True)

        super_annotations = {}
        if len(cls.__mro__) > 1:
            super_cls = cls.__mro__[1]
            if hasattr(super_cls, 'annotations'):
                super_annotations = super_cls.annotations()

        return {**super_annotations, **this_annotations}


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
        # Convert each value in the list to the nested type
        nested_type_hint = get_args(type_hint)[0]
        return [_convert(v, nested_type_hint) for v in value]
    
    elif get_origin(type_hint) is UnionType:
        # Manage optional types (e.g. Payout | None)
        optional_type, none_type = get_args(type_hint)
        if none_type is type(None):
            return _convert(value, optional_type)
        
    elif issubclass(type_hint, StockXBaseModel):
        # Conver the nested JSON to the type hinted model
        return type_hint.from_json(value)
    
    else:
        return type_hint(value)