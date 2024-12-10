from __future__ import annotations

from collections.abc import (
    Awaitable, 
    Callable, 
    Mapping, 
    Sequence
)
from typing import TypeVar


__all__ = (
    'Params',
    'JSON',
    'ComputedValue',
    'computed_value',
)

_JSONPrimitive = str | int | float | bool | None
"""Type alias for JSON primitive values."""

Params = Mapping[str, _JSONPrimitive]
"""Type alias for parameter mappings with JSON primitive values."""

type JSON = Mapping[str, _JSONPrimitive | Sequence[_JSONPrimitive] | JSON]
"""Type alias for JSON-like structures."""


I = TypeVar('I')
O = TypeVar('O')

type ComputedValue[I, O] = O | Callable[[I], O] | Callable[[I], Awaitable[O]]
"""
Type alias for computed values that can be:
    - Direct value of type `O`  
    - Synchronous function that takes `I` and returns `O`
    - Asynchronous function that takes `I` and returns `O`
"""

async def computed_value(input: I, value: ComputedValue[I, O]) -> O:
    """Resolve a `ComputedValue` given an input."""
    if callable(value):
        try:
            return await value(input)
        except TypeError:
                return value(input)
    else:
        return value