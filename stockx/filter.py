from __future__ import annotations

from collections.abc import Iterable, Callable
from typing import TypeVar, Any, Generic


T = TypeVar('T')


class Filter(Generic[T]):
    def __init__(
            self,
            class_: type[T],
            getter: Callable[[T], Any],
            condition: Callable[[Any, set[Any]], bool],
    ) -> None:
        self.class_ = class_
        self.extractor = getter
        self.condition = condition
        self.allowed_values = set()

    def include(self, values: Iterable[Any]) -> None:
        if not values:
            return
        self.allowed_values.update(values)

    def apply(self, values: Iterable[Any]) -> None:
        if not values:
            return
        if self.allowed_values:
            self.allowed_values.intersection_update(values)
        else:
            self.allowed_values.update(values)

    def match(self, obj: T) -> bool:
        if not self.allowed_values:
            return True
        value = self.extractor(obj)
        return self.condition(value, self.allowed_values)
    
    def empty(self) -> bool:
        return not self.allowed_values
    

def create_filter(
    class_: type[T],
    /,
    getter: Callable[[T], Any],
    condition: Callable[[Any, set[Any]], bool],
) -> Filter[T]:
    return Filter(class_, getter, condition)

