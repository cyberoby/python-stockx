from __future__ import annotations

from collections.abc import (
    Awaitable, 
    Callable, 
    Mapping, 
    Sequence
)
from typing import TypeVar


JSONPrimitive = str | int | float | bool | None
Params = Mapping[str, JSONPrimitive]
type JSON = Mapping[str, JSONPrimitive | Sequence[JSONPrimitive] | JSON]


I = TypeVar('I')
O = TypeVar('O')

type ComputedValue[I, O] = O | Callable[[I], O] | Callable[[I], Awaitable[O]]

async def computed_value(input: I, value: ComputedValue[I, O]) -> O:
    if callable(value):
        try:
            return await value(input)
        except TypeError:
                return value(input)
    else:
        return value