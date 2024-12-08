from collections.abc import Iterable
from dataclasses import (
    Field, 
    fields, 
    is_dataclass,
)
from datetime import datetime


def iso(datetime: datetime | None) -> str | None:
    if not datetime:
        return None
    return f'{datetime.isoformat(timespec='seconds')}.000Z'


def comma_separated(values: Iterable[str] | None) -> str | None:
    return ','.join(values) if values else None


def iso_date(datetime: datetime | None) -> str | None:
    return datetime.strftime('%Y-%m-%d') if datetime else None


def pretty_str(cls: type) -> type:
    """Decorator that adds pretty-printing functionality to a dataclass."""

    if not is_dataclass(cls):
        raise ValueError(f'{cls} is not a dataclass.')

    original_str = cls.__str__

    def __str__(self, level: int = 0) -> str:
        if getattr(self, '__pretty_str_enabled__', False) == False:
            return original_str(self)

        indent = '  ' * level

        def format(value, level):
            if getattr(value, '__pretty_str_enabled__', False) == True:
                # Increase the indentation level and add a newline
                return f'\n{value.__str__(level + 1)}'
            elif (
                isinstance(value, Iterable) 
                and not isinstance(value, (str, bytes, bytearray))
            ):
                # Increase the indentation level and join the items
                return f', '.join(format(item, level + 1) for item in value)
            else:
                # Return the value as a string
                return str(value)
        
        def value(field: Field):
            return getattr(self, field.name)

        attributes = '\n'.join(
            f'{indent}  {field.name}: {format(value(field), level + 1)}'
            for field in fields(self)
        )

        return f'{indent}{self.__class__.__name__}:\n{attributes}'
    
    setattr(cls, '__pretty_str_enabled__', True)
    setattr(cls, '__str__', __str__)

    return cls
