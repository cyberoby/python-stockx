from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from stockx.utils import json_to_snake


@dataclass
class Response:
    status_code: int
    message: str = ''
    data: dict | list[dict] = field(default_factory=list)


@dataclass
class StockXBaseModel:

    _numeric_fields: tuple[str] = field(
        default=(), 
        init=False, 
        repr=False
    )
    _datetime_fields: tuple[str] = field(
        default=(), 
        init=False,
        repr=False
    )
    _object_fields: tuple[tuple[str, StockXBaseModel]] = field(
        default=(), 
        init=False, 
        repr=False
    )
    _list_fields: tuple[tuple[str, StockXBaseModel]] = field(
        default=(), 
        init=False, 
        repr=False
    )

    def __post_init__(self) -> None:
        self._convert_datetime()
        self._convert_numeric()
        self._convert_objects()
        self._convert_list()

    @classmethod
    def from_json(cls, json: dict) -> StockXBaseModel:
        snake_kwargs = json_to_snake(json).items() 
        matching_kwargs = {
            key: value for key, value in snake_kwargs
            if key in cls.__match_args__
        }
        return cls(**matching_kwargs)
    
    def _convert(self, fields: tuple[str], conversion_func: function) -> None:
        for field in fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, conversion_func(value))
    
    def _convert_numeric(self) -> None:
        self._convert(self._numeric_fields, lambda x: float(x))

    def _convert_datetime(self) -> None:
        self._convert(self._datetime_fields, lambda x: datetime.fromisoformat(x))

    def _convert_objects(self) -> None:
        for field, model in self._object_fields:
            self._convert((field,), conversion_func=model.from_json)

    def _convert_list(self) -> None:
        for field, model in self._list_fields:
            json_list = getattr(self, field, [])
            objects_list = [model.from_json(item) for item in json_list]
            setattr(self, field, objects_list)

